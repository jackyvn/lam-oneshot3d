# Introduction 
This project creates a depth map from a 2D image to generate a 3D image. 
It uses AWS Lambda and ECR for deployment.

# License
This project is licensed under the MIT License.

# The Dockerfile
The Dockerfile starts with an AWS base image, installs dependencies and includes the handler source code. 
The final Docker image size is about 3.78GB.
```dockerfile
FROM public.ecr.aws/lambda/python:3.8

COPY . ./
RUN python3.8 -m pip install -r requirements.txt -t .
RUN yum install libGL libgomp -y
CMD ["app.lambda_handler"]

```

# Build and Push to ECR
To build and push the Docker image to ECR, follow these steps:
1. Run the following command to authenticate Docker with your Amazon ECR registry:
   ```bash 
   aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin YOURACCOUNTID.dkr.ecr.us-east-1.amazonaws.com
   ```
2. Build the Docker image with the following command:
   ```bash 
   docker build -t lam-oneshot3d .
   ```
3. Tag the Docker image with the following command:
   ```bash 
   docker tag lam-oneshot3d:latest YOURACCOUNTID.dkr.ecr.ap-northeast-1.amazonaws.com/lam-oneshot3d:latest
   ```
4. Push the Docker image to ECR with the following command:
   ```bash 
   docker push YOURACCOUNTID.dkr.ecr.us-east-1.amazonaws.com/lam-oneshot3d:latest
   ```

# Create Lambda Function
To create a Lambda Function using the Docker image in your ECR repository, follow these steps:

1. Go to the Lambda Console and create a new Lambda Function.
2. Choose "Container image" as the source for your function.
3. Browse for the latest lam-oneshot3d image in your AWS account and select it.
4. Leave the architecture as "x86_64" and continue. Note that you may need to wait 15-20 seconds between steps while configuring the function manually in the Console for the updates to apply.
5. Under "Configuration" -> "General Configuration", increase the memory limit to 512MB and increase the runtime timeout to 60 seconds. Save the changes.
6. Go to the Test tab for the function and create a new event.
7. Replace the "hello-world" JSON with the following test event:
```json
{
  "queryStringParameters": {
    "src": "Your Image URL"
  }
}
```
8. Save the event with a name of your choosing and click "Test". If it succeeds, you will get a bunch of Base64 text back.
9. If you would like to see the image, go to "Configuration" -> "Function URL" and click "Create Function URL" with "NONE" authentication. Be aware that you are opening your function up to the public internet by doing this, and are responsible for any costs if someone discovers your Function URL.
10. Copy your Function URL into a new browser window and append the source image to the query string with "?src=SOURCEURL" like this: https://xxx.lambda-url.ap-northeast-1.on.aws/?src=xxx.

Please note that this project is based on the [one_shot_3d_photography](https://github.com/facebookresearch/one_shot_3d_photography) repository by Facebook Research, and has been modified to work with AWS Lambda and ECR.