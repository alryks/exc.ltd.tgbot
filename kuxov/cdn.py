import io
import os
from pathlib import Path
from typing import Union

import boto3
import filetype
import requests
from PIL import Image
from bson import ObjectId
import tempfile


class CDN(object):
    def __init__(self, endpoint_url="http://213.219.215.209:9000",
                 aws_access_key_id="hnPkbztWeXCa7cpMJmeu",
                 aws_secret_access_key="9eYISaJQYGGNtthCHqnRbd6n90aZZ6YAqsbwLlXe",
                 bucket_name="kuxov",
                 public_url="http://213.219.215.209:9000/kuxov"):
        super(CDN, self).__init__()
        if public_url is None:
            public_url = endpoint_url

        self.s3 = boto3.resource(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        print("Use CDN.")
        print(f"Use {bucket_name}.")
        self.bucket = self.s3.Bucket(bucket_name)
        self.endpoint_url = endpoint_url
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
