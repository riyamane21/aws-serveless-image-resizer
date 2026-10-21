
import boto3
import json
import os
import urllib.parse
from io import BytesIO
from PIL import Image

s3 = boto3.client("s3")

OUTPUT_BUCKET = "riya-serverless-image-output-2026"

IMAGE_SIZES = {
    "thumbnail": (150, 150),
    "medium": (500, 500),
    "large": (1000, 1000),
}

def lambda_handler(event, context):
    for record in event["Records"]:
        input_bucket = record["s3"]["bucket"]["name"]
        image_key = urllib.parse.unquote_plus(
            record["s3"]["object"]["key"]
        )

        # Process images only
        if not image_key.lower().endswith(
            (".jpg", ".jpeg", ".png")
        ):
            print(f"Skipping unsupported file: {image_key}")
            continue

        # Download the original image into memory
        response = s3.get_object(
            Bucket=input_bucket,
            Key=image_key
        )
        image_data = response["Body"].read()

        with Image.open(BytesIO(image_data)) as original:
            original.load()

            for size_name, dimensions in IMAGE_SIZES.items():
                resized = original.copy()
                resized.thumbnail(dimensions)

                output_buffer = BytesIO()

                # Convert palette or unusual image modes when needed
                if resized.mode not in ("RGB", "RGBA"):
                    resized = resized.convert("RGB")

                output_format = (
                    "PNG"
                    if image_key.lower().endswith(".png")
                    else "JPEG"
                )

                resized.save(
                    output_buffer,
                    format=output_format,
                    optimize=True
                )
                output_buffer.seek(0)

                base_name = os.path.splitext(
                    os.path.basename(image_key)
                )[0]

                extension = "png" if output_format == "PNG" else "jpg"
                output_key = (
                    f"{size_name}/{base_name}_{size_name}.{extension}"
                )

                s3.put_object(
                    Bucket=OUTPUT_BUCKET,
                    Key=output_key,
                    Body=output_buffer.getvalue(),
                    ContentType=(
                        "image/png"
                        if output_format == "PNG"
                        else "image/jpeg"
                    )
                )

                print(
                    f"Created s3://{OUTPUT_BUCKET}/{output_key}"
                )

    return {
        "statusCode": 200,
        "body": json.dumps(
            "Image resizing completed successfully"
        )
    }
