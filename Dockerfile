FROM public.ecr.aws/lambda/python:3.8

COPY . ./
RUN python3.8 -m pip install -r requirements.txt -t .
RUN yum install libGL libgomp -y
CMD ["app.lambda_handler"]
