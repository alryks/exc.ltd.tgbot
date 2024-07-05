import io
import os
from pathlib import Path
from typing import Union

import boto3
import requests
from PIL import Image
from bson import ObjectId
import tempfile

from .scenario import CDN_BUCKET, CDN_REGION, CDN_ENDPOINT, CDN_ACCESS_KEY_ID, CDN_SECRET_ACCESS_KEY


class CDN(object):
    def __init__(self):
        super(CDN, self).__init__()

        public_url = f"{CDN_ENDPOINT}/{CDN_BUCKET}"

        self.s3 = boto3.resource(
            "s3",
            endpoint_url=CDN_ENDPOINT,
            aws_access_key_id=CDN_ACCESS_KEY_ID,
            aws_secret_access_key=CDN_SECRET_ACCESS_KEY,
        )

        print("Using CDN.")
        print(f"Using {CDN_BUCKET}.")
        self.bucket = self.s3.Bucket(CDN_BUCKET)
        self.endpoint_url = CDN_ENDPOINT
        self.public_url = public_url

    def host_photo(self, photo: Image.Image):
        with tempfile.TemporaryDirectory() as temp_dir:
            photo_path = os.path.join(temp_dir, "1.jpg")
            photo.save(photo_path, format="JPEG")
            return self.host(Path(photo_path))

    def retrieve_photo(self, _id: ObjectId):
        url = self.url_for(_id)
        return Image.open(io.BytesIO(requests.get(url).content)).convert('RGB')

    def retrieve_content(self, _id: ObjectId):
        url = self.url_for(_id)
        return requests.get(url).content

    def host(self, path: Union[io.BufferedReader, Path]):
        _id = ObjectId()
        path = Path(path)
        with path.open("rb") as f:
            self.bucket.put_object(Key=str(_id) + '.jpg',
                                   Body=f,
                                   ContentType='image/jpeg')
        return _id

    def url_for(self, _id: ObjectId):
        _id = ObjectId(_id)
        return os.path.join(self.public_url,
                            str(_id) + '.jpg')

    def list(self):
        return [ObjectId(obj.key)
                for obj in self.bucket.objects.all()]

    def delete(self, *_id: ObjectId):
        self.bucket.delete_objects(Delete={
            'Objects': [
                {
                    'Key': str(each_id) + '.jpg',
                }
                for each_id in _id[:1000]
            ],
            'Quiet': True
        },)
        if len(_id) > 1000:
            self.delete(*_id[1000:])

    def getsize(self, _id: ObjectId) -> int:
        obj = self.bucket.Object(key=str(_id) + '.jpg')
        return obj.content_length

    def ping(self):
        return {
            "status": "ok"
        }
