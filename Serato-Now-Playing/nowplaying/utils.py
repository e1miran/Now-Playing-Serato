#!/usr/bin/env python3
''' handler to read the metadata from various file formats '''

#
# For now, this module is primarily a wrapper around tinytag
# with the idea that in the future there may be multiple
# engines or custom handling (pull tags from mixxing software?)
#

import io
import os
import sys

import imghdr
import jinja2
import tinytag


class TemplateHandler():  # pylint: disable=too-few-public-methods
    ''' Set up a template  '''
    def __init__(self, filename=None):
        self.envdir = envdir = None
        self.template = None

        if not filename:
            return

        if os.path.exists(filename):
            envdir = os.path.dirname(filename)
        else:
            return

        if not self.envdir or self.envdir != envdir:
            self.envdir = envdir
            self.env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(self.envdir),
                autoescape=jinja2.select_autoescape(['htm', 'html', 'xml']))

        basename = os.path.basename(filename)

        self.template = self.env.get_template(basename)

    def generate(self, metadatadict=None):
        ''' get the generated template '''
        if self.template:
            return self.template.render(metadatadict)
        return "No template found; check your settings"


def getmoremetadata(metadata=None):
    ''' given a chunk of metadata, try to fill in more '''

    if not metadata or 'filename' not in metadata:
        return metadata

    # tinytag is pure python and supports a wide variety of
    # formats.  because of that, it doesn't necessarily
    # have all the bells and whistles of other, more specific
    # libraries.  But this is good enough for us.

    if not os.path.isfile(metadata['filename']):
        return metadata

    tag = tinytag.TinyTag.get(metadata['filename'], image=True)

    for key in [
            'album', 'albumartist', 'artist', 'bitrate', 'bpm', 'composer',
            'disc', 'disc_total', 'genre', 'key', 'publisher', 'lang', 'title',
            'track', 'track_total', 'year'
    ]:
        if key not in metadata and hasattr(tag, key) and getattr(tag, key):
            metadata[key] = getattr(tag, key)

    if 'coverimageraw' not in metadata:
        coverimage = tag.get_image()

        if coverimage:
            metadata['coverimageraw'] = coverimage
            iostream = io.BytesIO(metadata['coverimageraw'])
            headertype = imghdr.what(iostream)
            if headertype == 'jpeg':
                headertype = 'jpg'
            metadata['coverimagetype'] = headertype
            metadata['coverurl'] = f'/cover.{headertype}'
    return metadata


def writetxttrack(filename=None, templatehandler=None, metadata=None):
    ''' write new track info '''
    if templatehandler:
        txttemplate = templatehandler.generate(metadata)
    else:
        txttemplate = '{{ artist }} - {{ title }}'

    with open(filename, "w") as textfh:
        #print("writing...")
        textfh.write(txttemplate)


def update_javascript(serverdir='/tmp', templatehandler=None, metadata=None):
    ''' update the image with the new info '''

    # This should really use a better templating engine,
    # but let us keep it simple for now

    indexhtm = os.path.join(serverdir, "index.htm")

    if not templatehandler:
        # absolutely require a template
        return

    titlecardhtml = templatehandler.generate(metadata)
    with open(indexhtm, "w") as indexfh:
        indexfh.write(titlecardhtml)

    if 'coverimageraw' in metadata:
        extension = metadata['coverimagetype']  # probably png or jpg
        with open(f'cover.{extension}', "wb") as coverfh:
            coverfh.write(metadata['coverimageraw'])


def main():
    ''' entry point as a standalone app'''
    metadata = {}
    metadata['filename'] = sys.argv[1]
    metadata = getmoremetadata(metadata)
    print(metadata)


if __name__ == "__main__":
    main()
