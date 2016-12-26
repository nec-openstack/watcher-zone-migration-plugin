#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from glanceclient import client as glanceclient
from glanceclient import exc as glance_exections


def glance_client(session):
    return glanceclient.Client('1', session=session)


def get_image(glance, name_or_id):
    try:
        image = glance.images.get(name_or_id)
        return image
    except glance_exections.HTTPNotFound:
        images = glance.images.list()
        _images = []
        for image in images:
            if image.name == name_or_id:
                _images.append(image)
        if len(_images) == 0:
            raise ValueError('Image not Found: %s' % name_or_id)
        if len(_images) > 1:
            raise ValueError('Image name seems ambiguous: %s' % name_or_id)
        return _images[0]
