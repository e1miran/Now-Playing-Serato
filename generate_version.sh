#!/usr/bin/env bash

VERSION=$(git describe --always --tags)

echo "Found ${VERSION}"

cat <<EOF > nowplaying/version.py
#!/usr/bin/env python3
''' automatically generated version file during CI builds
    this is built from the generate_version.sh file in the
    root of the source tree.
'''

VERSION = '${VERSION}'
EOF
