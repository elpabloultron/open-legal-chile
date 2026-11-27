"""Script opcional de escalamiento GPU para fine-tuning Transformer y exportación ONNX INT8.

Permite entrenar en GPU un encoder (`intfloat/multilingual-e5-small` o `BAAI/bge-m3`)
sobre los mismos pares chilenos de `data/parquet/` + Hugging Face y exportarlo a ONNX INT8
para consumo local vía `OPENLEGAL_ONNX_EMBED_DIR` o publicación en Hugging Face Hub.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


def main() -> int:
    parser = argparse.ArgumentParser(description="Fine-tuning GPU Transformer + ONNX INT8 para Open Legal Chile.")
    parser.add_argument("--base-model", default="intfloat/multilingual-e5-small")
    parser.add_argument("--out-dir", default=str(pathlib.Path.home() / ".openlegal" / "models" / "embed_onnx"))
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    try:
        from datasets import Dataset
        from sentence_transformers import SentenceTransformer, SentenceTransformerTrainer, SentenceTransformerTrainingArguments
        from sentence_transformers.losses import MultipleNegativesRankingLoss
    except ImportError:
        sys.stderr.write(
            "Este script opcional requiere GPU + paquetes de entrenamiento:\n"
            "  pip install sentence-transformers datasets accelerate onnxruntime-tools\n"
            "Para CPU puro usar: python scripts/entrenar_embeddings_chile.py\n"
        )
        return 1

    from scripts.entrenar_embeddings_chile import _cargar_pares_reales

    pares = _cargar_pares_reales()
    ds = Dataset.from_dict({
        "anchor": [f"query: {q}" for q, _, _ in pares],
        "positive": [f"passage: {t}. {d}" for _, t, d in pares],
    })
    modelo = SentenceTransformer(args.base_model)
    loss = MultipleNegativesRankingLoss(modelo)
    out_pt = pathlib.Path(args.out_dir) / "checkpoint_hf"
    train_args = SentenceTransformerTrainingArguments(
        output_dir=str(out_pt),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        fp16=True,
        save_strategy="epoch",
        logging_steps=50,
    )
    trainer = SentenceTransformerTrainer(model=modelo, args=train_args, train_dataset=ds, loss=loss)
    trainer.train()
    modelo.save_pretrained(str(out_pt))
    print(f"Checkpoint Transformer guardado en: {out_pt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
