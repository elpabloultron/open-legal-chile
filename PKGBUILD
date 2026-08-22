# Maintainer: Open Legal Chile Team <contacto@openlegal.cl>
pkgname=openlegal-chile-bin
pkgver=1.0.0
pkgrel=1
pkgdesc="Suite de Inteligencia Jurídica y Conectores Oficiales del Estado de Chile"
arch=('x86_64' 'aarch64')
url="https://github.com/open-legal-chile"
license=('Apache-2.0')
depends=('python' 'webkit2gtk')
source=("git+https://github.com/open-legal-chile/open-legal-chile.git")
sha256sums=('SKIP')

build() {
    cd "$srcdir"
    pip install -e .
}

package() {
    cd "$srcdir"
    install -Dm755 OpenLegalChile "$pkgdir/usr/bin/openlegal-desktop"
    install -Dm644 openlegal.desktop "$pkgdir/usr/share/applications/openlegal.desktop"
}
