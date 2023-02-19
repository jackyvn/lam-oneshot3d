#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import base64
import json

import caffe2.python
import caffe2.python.workspace as ws
import cv2
import numpy as np
import os
from io import BytesIO
from PIL import Image
import requests

from visualization import visualize_depth


class DepthEstimatorCaffe2:
    def __init__(self, init_net_file: str, predict_net_file: str):
        print(f"Creating Tiefenrausch model from files...")
        print(f"  Init net: '{init_net_file}'")
        print(f"  Predict net: '{predict_net_file}'")

        self.init_net = caffe2.proto.caffe2_pb2.NetDef()
        with open(init_net_file, "rb") as finit:
            self.init_net.ParseFromString(finit.read())

        self.predict_net = caffe2.proto.caffe2_pb2.NetDef()
        with open(predict_net_file, "rb") as fpred:
            self.predict_net.ParseFromString(fpred.read())

    def estimate_depth(
        self, src_file: str, out_file: str, vis_file: str = None
    ):
        print(f"Reading image file '{src_file}'...")
        bgr_image = cv2.imread(src_file)
        rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)

        # Downscale image
        target_max_dimension = 384
        h, w, _ = rgb_image.shape
        if h > w:
            nh = target_max_dimension
            nw = int(w * nh / h)
        else:
            nw = target_max_dimension
            nh = int(h * nw / w)

        nw -= nw % 32
        nh -= nh % 32

        rgb_image = cv2.resize(rgb_image, (nw, nh), interpolation=cv2.INTER_AREA)

        # Predict depth
        input = np.transpose(rgb_image / 255.0, (2, 0, 1))
        input = input[np.newaxis, :, :, :].astype(np.float32)
        ws.ResetWorkspace()
        # ws.FeedBlob("0", input)
        ws.FeedBlob(self.predict_net.external_input[0], input)
        ws.CreateNet(self.init_net)
        ws.CreateNet(self.predict_net)
        ws.RunNet(self.init_net.name)
        ws.RunNet(self.predict_net.name)
        output_blob = self.predict_net.external_output[0]
        output = ws.FetchBlob(output_blob)
        disparity = np.exp(output.squeeze())

        if vis_file is not None:
            print("Visualizing depth.....")
            vis = visualize_depth(disparity)
            # return vis
            print(f"Writing visualization file '{vis_file}'...")
            os.makedirs(os.path.dirname(vis_file), exist_ok=True)
            cv2.imwrite(vis_file, vis)


def lambda_handler(event, context):
    print(f"Event: {event}")
    src = ''
    if 'queryStringParameters' in event:
        src = event['queryStringParameters'].get('src', '')
    if src == '':
        return {
            'headers': {"Content-Type": "application/json"},
            'statusCode': 400,
            'body': json.dumps({'error': 'bad request'})
        }

    try:
        input = requests.get(src, allow_redirects=True)
        # Save input image to /tmp
        img = Image.open(BytesIO(input.content))
        img.save("/tmp/input_image.jpg")

        args = {
            "init_net": "model/tiefenrausch_init.pb",
            "predict_net": "model/tiefenrausch.pb",
            "src_file": "/tmp/input_image.jpg",
            "out_file": "/tmp/output_image.npy",
            "vis_file": "/tmp/output_image.png"
        }

        depth_estimator = DepthEstimatorCaffe2(args["init_net"], args["predict_net"])

        if args["src_file"] is not None:
            depth_estimator.estimate_depth(
                args["src_file"], args["out_file"], args["vis_file"])

            # Convert image to base64
            img = Image.open(args["vis_file"])
            im_file = BytesIO()
            img.save(im_file, format="PNG")
            im_bytes = im_file.getvalue()  # im_bytes: image in binary format.
            base64_img = base64.b64encode(im_bytes)

            response = {
                'headers': {"Content-Type": "image/png"},
                'statusCode': 200,
                'body': base64_img.decode('utf-8'),
                'isBase64Encoded': True
            }
            print(f"Response: \n {response}")

            return response

        print("Finished.")
    except Exception as ex:
        print(f"Exception: {ex}")
        return {
            'headers': {"Content-Type": "application/json"},
            'statusCode': 500,
            'body': json.dumps({'error': ex.__repr__()})
        }


# if __name__ == '__main__':
#     event = {
#         "resource": "/{proxy+}",
#         # "path": request.path,
#         # "httpMethod": request.method,
#         # "headers": request.headers,
#         "multiValueHeaders": {
#             "Accept": [
#                 "*/*"
#             ],
#             "Accept-Encoding": [
#                 "gzip, deflate, br"
#             ],
#             "Content-Type": [
#                 "application/json"
#             ],
#             "Host": [
#                 "f5yps7assf.execute-api.us-east-1.amazonaws.com"
#             ],
#             "Postman-Token": [
#                 "e5afdc3e-bcd0-4451-9808-230bcc60fdd2"
#             ],
#             "User-Agent": [
#                 "PostmanRuntime/7.28.0"
#             ],
#             "X-Amzn-Trace-Id": [
#                 "Root=1-60a780f7-059620dc1a93d52f34f73980"
#             ],
#             "X-Forwarded-For": [
#                 "118.69.74.12", "118.69.74.12"
#             ],
#             "X-Forwarded-Port": [
#                 "443"
#             ],
#             "X-Forwarded-Proto": [
#                 "https"
#             ]
#         },
#         "multiValueQueryStringParameters": None,
#         "pathParameters": {
#             "proxy": "test"
#         },
#         "stageVariables": "None",
#         "requestContext": {
#             "resourceId": "wm16n6",
#             "resourcePath": "/{proxy+}",
#             "httpMethod": "POST",
#             "extendedRequestId": "frEWqHxioAMFt4A=",
#             "requestTime": "21/May/2021:09:44:23 +0000",
#             "path": "/devapi/test",
#             "accountId": "734932696578",
#             "protocol": "HTTP/1.1",
#             "stage": "devapi",
#             "domainPrefix": "f5yps7assf",
#             "requestTimeEpoch": 1621590263306,
#             "requestId": "c9cf35cd-654f-4788-962e-0c224f023f0c",
#             "identity": {
#                 "cognitoIdentityPoolId": "None",
#                 "accountId": "None",
#                 "cognitoIdentityId": "None",
#                 "caller": "None",
#                 "sourceIp": "118.69.74.12",
#                 "principalOrgId": "None",
#                 "accessKey": "None",
#                 "cognitoAuthenticationType": "None",
#                 "cognitoAuthenticationProvider": "None",
#                 "userArn": "None",
#                 "userAgent": "PostmanRuntime/7.28.0",
#                 "user": "None"
#             },
#             "domainName": "f5yps7assf.execute-api.us-east-1.amazonaws.com",
#             "apiId": "f5yps7assf"
#         },
#         "body": None,
#         "queryStringParameters": {
#             "src": "https://raw.githubusercontent.com/danielgatis/rembg/master/examples/animal-1.jpg"
#         },
#         "isBase64Encoded": False
#     }
#     lambda_handler(event, None)
