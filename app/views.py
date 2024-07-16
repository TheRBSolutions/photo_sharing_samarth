# gallery/views.py
# pylint: disable=no-member
import io
import json
import os
import re
from urllib.parse import urlparse
from django.contrib.auth.models import Group, User
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .decorators import admin_only, unauthenticated_user
from .forms import (
    AlbumForm,
    BusinessSettingsForm,
    CreateUserForm,
    MediaForm,
    PhotographerSettingsForm,
    UserProfileForm,
)
from .models import Album, Business, Media, StorageDetails, Subscription, UserProfile

from PIL import Image
from django.utils.crypto import get_random_string


@unauthenticated_user
def RegisterPage(request):
    form = CreateUserForm()
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            profile_group = form.cleaned_data.get("is_photographer")
            if profile_group:
                photographer_group = Group.objects.get(name="photographer")
                print("request.user+", request.user)
                user = User.objects.get(username=username)
                # admin_group.user_set.add(request.user)
                user.groups.add(photographer_group)
                print("User added to Photographer group.")
                # Business.objects.create(user = request.user, name = username)
                # print("Business Created")
            else:
                user_group = Group.objects.get(name="user")
                print("request.user+", request.user)
                user = User.objects.get(username=username)
                # admin_group.user_set.add(request.user)
                user.groups.add(user_group)
                print("User added to User group.")
            messages.success(request, "Account was created for " + username)

            return redirect("login")

    context = {"form": form}
    return render(request, "app/register.html", context)


@unauthenticated_user
def loginPage(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            return redirect("photographer_dashboard")

        else:
            messages.info(request, "Username OR password is incorrect")

    context = {}
    return render(request, "app/login.html", context)


def logoutUser(request):
    logout(request)
    return redirect("login")


from django.db.models.functions import TruncMonth
from django.db.models import Count
from django.db.models import Sum


# @login_required(login_url="login")
# @admin_only
# def home(request):
#     context = {}
#     return render(request, "app/dashboard.html", context)

from django.shortcuts import render, get_object_or_404, redirect


def photographer_dashboard(request):
    if request.user.is_authenticated:
        # Fetch all albums for the logged-in photographer
        albums = Album.objects.filter(photographer=request.user) # pylint: disable=no-member
        return render(request, "app/photographer_dashboard.html", {"albums": albums})
    else:
        return redirect("login")  # Redirect to login if user is not authenticated


def create_album(request):
    if request.method == "POST":
        form = AlbumForm(request.POST, request.FILES)
        if form.is_valid():
            album = form.save(commit=False)
            album.photographer = request.user
            album.save()
            messages.success(request, "Album Created Successfully!")
            return redirect("photographer_dashboard")
    else:
        form = AlbumForm()
    return render(request, "app/create_album.html", {"form": form})


@login_required(login_url="login")
def album_settings(request, id):
    album = get_object_or_404(Album, id=id)

    if request.method == "POST":
        form = AlbumForm(request.POST, request.FILES, instance=album)
        if form.is_valid():
            form.save()
            return redirect("photographer_dashboard")  # Redirect to a success page
    else:
        form = AlbumForm(instance=album)

    return render(request, "app/album_settings.html", {"form": form, "album": album})


import boto3
from botocore.config import Config

# Assuming you have set the AWS credentials in your environment variables
AWS_ACCESS_KEY_ID = "AKIA47CRZGZ7NIU6QAED"
AWS_SECRET_ACCESS_KEY = "psst0aroHZ9/70KtUuApXld1rQC9dEMc15Zz21J9"
# AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-west-2')  # Default to 'us-west-2' if not set

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name="ap-south-1",
)

# session = boto3.Session()
# s3_client = session.client("s3", config=Config(signature_version="s3v4"), verify=False)
# s3_resource = session.resource(
#     "s3", config=Config(signature_version="s3v4"), verify=False
# )

s3_client = session.client("s3", config=Config(signature_version="s3v4"), verify=False)
s3_resource = session.resource(
    "s3", config=Config(signature_version="s3v4"), verify=False
)
from collections import defaultdict

PLAN_UPLOAD_LIMITS = {
    "Free": 500,
    "Basic": 2000,
    "Premium": 5000,
}

from django.core.files.storage import default_storage

def upload_images(request, album_id):
    album = get_object_or_404(Album, pk=album_id)
    if request.method == 'POST':
        folder = request.POST.get('folder')
        new_folder = request.POST.get('new_folder')
        if new_folder:
            folder = new_folder
        
        for file in request.FILES.getlist('file'):
            folder_path = f'{album_id}/{folder}/'
            file_path = default_storage.save(folder_path + file.name, file)
        
        return JsonResponse({'message': 'Images uploaded successfully!'})
    return JsonResponse({'error': 'Invalid request'}, status=400)


from PIL import Image
from django.core.files.base import ContentFile
import io

@login_required(login_url="login")
# @admin_only
def album_detail(request, id):
    business, created = Business.objects.get_or_create(user=request.user)
    album = get_object_or_404(Album, id=id)
    user_folder = f"{request.user.username}/{album.id}/"
    s3_path = os.path.join("index_gallery/", user_folder)
    bucket_name = "kapturise-face-recognition-bucket"

    media_items = defaultdict(list)
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=s3_path)
        if "Contents" in response:
            for obj in response["Contents"]:
                folder_name = os.path.basename(os.path.dirname(obj["Key"]))
                url = s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket_name, "Key": obj["Key"]},
                    ExpiresIn=3600,
                )
                media_items[folder_name].append(url)
    except Exception as e:
        print("Credentials not available: ", e)

    profile = get_object_or_404(Profile, user=request.user)
    subscription, created = Subscription.objects.get_or_create(profile=profile)
    upload_limit = PLAN_UPLOAD_LIMITS.get(subscription.plan, 0)
    storage, created = StorageDetails.objects.get_or_create(profile=profile)
    current_uploads = storage.total_uploads

    if request.method == "POST":
        form = MediaForm(request.POST, request.FILES)
        files = request.FILES.getlist("file")
        total_new_uploads = current_uploads + len(files)

        if total_new_uploads > upload_limit:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Upload limit reached. Please upgrade your subscription to upload more media.",
                },
                status=403,
            )

        # Check both folder select and new folder inputs
        selected_folder = request.POST.get("folder_name", "").strip()
        new_folder = request.POST.get("new_folder", "").strip()
        
        folder_name = new_folder if new_folder else selected_folder

        if folder_name == "" or folder_name is None or folder_name == 'null':
            folder_name = "Main"
        folder_name = folder_name + "/"

        if form.is_valid():
            for file in files:
                # Save the original file
                original_filename, file_extension = os.path.splitext(file.name)
                original_filename = re.sub(
                    r"[^\w\s-]", "", original_filename
                )
                original_filename = re.sub(
                    r"\s+", "_", original_filename.strip().lower()
                )
                original_filename = f"{original_filename}{file_extension}"

                original_media = Media(file=file, album=album, folder_name="original_images/")
                original_media.save()

                original_s3_path = os.path.join(
                    "original_images/", original_filename
                )
                original_s3_object = s3_resource.Object(bucket_name, original_s3_path)
                file.seek(0)
                original_s3_object.put(
                    Body=file,
                    Metadata={
                        "FullName": os.path.splitext(original_filename)[0],
                        "UserName": request.user.username,
                        "albumId": str(album.id),
                        "FileName": original_filename,
                        "FolderName": "original_images",
                        "collectionId": f"kapturise_faces_collection_{request.user.username}_{album.id}",
                    },
                )

                # Compress the image
                image = Image.open(file)
                output = io.BytesIO()
                image.save(output, format='JPEG', quality=75)
                output.seek(0)

                # Create a Django ContentFile for the compressed image
                compressed_file = ContentFile(output.getvalue(), name=file.name)

                # Save the compressed file
                compressed_filename = re.sub(
                    r"[^\w\s-]", "", file.name
                )
                compressed_filename = re.sub(
                    r"\s+", "_", compressed_filename.strip().lower()
                )
                compressed_filename = f"{compressed_filename}{file_extension}"

                compressed_media = Media(file=compressed_file, album=album, folder_name=folder_name)
                compressed_media.save()

                compressed_s3_path = os.path.join(
                    "index_gallery/", user_folder, folder_name, compressed_filename
                )
                compressed_s3_object = s3_resource.Object(bucket_name, compressed_s3_path)
                compressed_s3_object.put(
                    Body=output.getvalue(),
                    Metadata={
                        "FullName": os.path.splitext(compressed_filename)[0],
                        "UserName": request.user.username,
                        "albumId": str(album.id),
                        "FileName": compressed_filename,
                        "FolderName": folder_name[:-1],
                        "collectionId": f"kapturise_faces_collection_{request.user.username}_{album.id}",
                    },
                )

            storage.total_uploads = total_new_uploads
            storage.save()

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Please wait while files are uploading...",
                }
            )
    else:
        form = MediaForm()

    sorted_media_items = {}
    if "Main" in media_items:
        sorted_media_items["Main"] = media_items.pop("Main")
    sorted_media_items.update(media_items)

    return render(
        request,
        "app/album_detail.html",
        {
            "album": album,
            "media_items": dict(sorted_media_items),
            "form": form,
            "album_id": id,
            "business": business,
        },
    )



@login_required(login_url="login")
@admin_only
def save_image_details(request):
    if request.method == "POST":
        image_url = request.POST.get("image_url")
        description = request.POST.get("description")
        tags = request.POST.get("tags")

        # Implement logic to save description and tags for the image
        # This might involve updating a database record or adding metadata to the S3 object

        return JsonResponse({"status": "success", "message": "Image details saved successfully."})
    return JsonResponse({"status": "error", "message": "Invalid request method."})
# def shared_album_detail(request, id):
#     album = get_object_or_404(Album, id=id)
#     media_items = Media.objects.filter(album=album)

#     profile_id = request.session.get('profile_id')
#     unique_token = request.session.get('unique_token')

#     if not profile_id or not unique_token:
#         return redirect('upload_selfie', id=id)

#     user_profile = UserProfile.objects.filter(id=profile_id, user_for_album=album).first()
#     matched_photos = []

#     if user_profile and user_profile.encoded_face:
#         user_encoding = np.array(json.loads(user_profile.encoded_face), dtype=np.float64)

#         for media in media_items:
#             image_path = media.file.path
#             with open(image_path, 'rb') as media_file:
#                 image = Image.open(media_file)
#                 image = image.convert('RGB')
#                 image = np.array(image)
#                 face_locations = face_recognition.face_locations(image)
#                 face_encodings = face_recognition.face_encodings(image, face_locations)

#                 for face_encoding in face_encodings:
#                     match = face_recognition.compare_faces([user_encoding], face_encoding)
#                     if match[0]:
#                         matched_photos.append(media)
#                         break

#     return render(request, 'app/shared_album_details.html', {'album': album, 'media_items': media_items, 'matched_photos': matched_photos})


import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create a custom configuration with SSL verification disabled
config = Config(
    # signature_version="s3v4",
    region_name="ap-south-1",
    retries={"max_attempts": 10, "mode": "standard"},
)
from botocore.exceptions import NoCredentialsError

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name="ap-south-1",
)
# Initialize Rekognition and DynamoDB clients with SSL verification disabled
rekognition = session.client("rekognition", config=config, verify=False)
dynamodb = session.client("dynamodb", config=config, verify=False)
s3 = session.client("s3", config=config, verify=False)
dynamodb_client = session.client("dynamodb", config=config, verify=False)
# s3_client = session.client('s3', config=Config(signature_version='s3v4'), verify=False)


def shared_album_detail(request, id):
    album = get_object_or_404(Album, id=id)
    user_folder = f"{album.photographer.username}/{album.id}/"
    s3_path = os.path.join("index_gallery/", user_folder)
    bucket_name = "kapturise-face-recognition-bucket"
    business = Business.objects.get(user = album.photographer)
    media_items = defaultdict(list)
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=s3_path)
        if "Contents" in response:
            for obj in response["Contents"]:
                folder_name = os.path.basename(os.path.dirname(obj["Key"]))
                url = s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket_name, "Key": obj["Key"]},
                    ExpiresIn=3600,
                )
                media_items[folder_name].append(url)
    except NoCredentialsError:
        print("Credentials not available")

    profile_id = request.session.get("profile_id")
    unique_token = request.session.get("unique_token")

    if not profile_id or not unique_token:
        return redirect("upload_selfie", id=id)

    user_profile = UserProfile.objects.filter(
        id=profile_id, user_for_album=album
    ).first()
    matched_photos = []

    if user_profile.selfie:
        image = Image.open(user_profile.selfie)
        stream = io.BytesIO()
        image.save(stream, format="JPEG")
        image_binary = stream.getvalue()

        response = rekognition.search_faces_by_image(
            CollectionId=f"kapturise_faces_collection_{album.photographer.username}_{album.id}",
            Image={"Bytes": image_binary},
            MaxFaces=10,
            FaceMatchThreshold=80,
        )

        for match in response["FaceMatches"]:
            image_id = match["Face"]["ImageId"]
            face = dynamodb.get_item(
                TableName="kapturise_faces_collection",
                Key={"RekognitionId": {"S": image_id}},
            )

            if "Item" in face and "FullName" in face["Item"]:
                userName = face["Item"]["UserName"]["S"]
                albumId = face["Item"]["albumId"]["S"]
                fileName = face["Item"]["FileName"]["S"]
                folderName = (
                    face["Item"].get("FolderName", {}).get("S", "")
                )  # Get folder name if it exists

                # Debug print statements
                print(f"UserName: {userName}")
                print(f"AlbumId: {albumId}")
                print(f"FileName: {fileName}")
                print(f"FolderName: {folderName}")

                if folderName:
                    image_key = (
                        f"index_gallery/{userName}/{albumId}/{folderName}/{fileName}"
                    )
                else:
                    image_key = f"index_gallery/{userName}/{albumId}/{fileName}"

                print(f"Image Key: {image_key}")

                try:
                    url = s3.generate_presigned_url(
                        "get_object",
                        Params={
                            "Bucket": "kapturise-face-recognition-bucket",
                            "Key": image_key,
                        },
                        ExpiresIn=3600,
                    )
                    matched_photos.append(url)
                except NoCredentialsError:
                    print("Credentials not available")
    print(media_items)
    sorted_media_items = {}
    if "Main" in media_items:
        sorted_media_items["Main"] = media_items.pop("Main")
    sorted_media_items.update(media_items)
    return render(
        request,
        "app/shared_album_details.html",
        {
            "album": album,
            "business":business,
            "media_items": dict(sorted_media_items),
            "matched_photos": matched_photos,
        },
    )


from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


@require_POST
@csrf_exempt  # Exempt CSRF for this example, but use CSRF tokens in production for security
def delete_image(request):
    data = json.loads(request.body)
    image_url = data["image_url"]

    # Extract the S3 key from the URL
    parsed_url = urlparse(image_url)
    bucket_name = "kapturise-face-recognition-bucket"
    key = parsed_url.path.lstrip("/")
    print(key)
    try:
        # Delete the object from S3
        s3_client.delete_object(Bucket=bucket_name, Key=key)
        file_name = key.split("/")[-1]
        print(file_name)
        # Retrieve the item from DynamoDB to get the RekognitionId
        response = dynamodb_client.scan(
            TableName="kapturise_faces_collection",
            FilterExpression="FileName = :file_name",
            ExpressionAttributeValues={":file_name": {"S": file_name}},
        )

        if "Items" in response and len(response["Items"]) > 0:
            item = response["Items"][0]
            rekognition_id = item["RekognitionId"]["S"]
            print(rekognition_id)
            # Delete the corresponding item from DynamoDB using RekognitionId
            dynamodb_client.delete_item(
                TableName="kapturise_faces_collection",
                Key={"RekognitionId": {"S": rekognition_id}},
            )

        return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@require_POST
@csrf_exempt
def delete_all_images(request):
    data = json.loads(request.body)
    album_id = data.get("album_id")

    try:
        # Delete all images from S3
        bucket_name = "kapturise-face-recognition-bucket"
        paginator = s3_client.get_paginator("list_objects_v2")
        response_iterator = paginator.paginate(
            Bucket=bucket_name,
            Prefix=f"index_gallery/{request.user.username}/{album_id}/",
        )

        for response in response_iterator:
            if "Contents" in response:
                for obj in response["Contents"]:
                    s3_client.delete_object(Bucket=bucket_name, Key=obj["Key"])

        # Delete entries from DynamoDB
        paginator = dynamodb_client.get_paginator("scan")
        response_iterator = paginator.paginate(
            TableName="kapturise_faces_collection",
            FilterExpression="begins_with(UserName, :username) AND begins_with(albumId, :album_id)",
            ExpressionAttributeValues={
                ":username": {"S": request.user.username},
                ":album_id": {"S": album_id},
            },
        )

        for response in response_iterator:
            if "Items" in response:
                for item in response["Items"]:
                    rekognition_id = item["RekognitionId"]["S"]
                    dynamodb_client.delete_item(
                        TableName="kapturise_faces_collection",
                        Key={"RekognitionId": {"S": rekognition_id}},
                    )

        return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


from .models import Profile


@login_required(login_url="login")
def photographer_settings(request):
    user = request.user
    profile = get_object_or_404(Profile, user=user)

    if request.method == "POST":
        form = PhotographerSettingsForm(request.POST, instance=profile, user=user)
        if form.is_valid():
            form.save()
            return redirect("photographer_dashboard")  # Redirect to a success page
    else:
        form = PhotographerSettingsForm(instance=profile, user=user)

    # Fetch storage and subscription details
    storage, _ = StorageDetails.objects.get_or_create(profile=profile)
    subscription = get_object_or_404(Subscription, profile=profile)

    # Update storage details
    storage.update_storage("kapturise-face-recognition-bucket")
    print(storage.total_uploads)

    album_count = Album.objects.filter(photographer=user).count()
    storage.total_albums = album_count
    storage.save()

    return render(
        request,
        "app/photographer_settings.html",
        {"form": form, "storage": storage, "subscription": subscription},
    )


def upgrade_subscription(request):
    return render(request, "app/pricing.html")


def upload_selfie(request, id):
    album = get_object_or_404(Album, id=id)
    business = Business.objects.get(user = album.photographer)
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            user_profile = form.save(commit=False)
            user_profile.user_for_album = album
            user_profile.save()

            # Generate a unique token for the session
            unique_token = get_random_string(length=32)
            request.session["profile_id"] = user_profile.id
            request.session["unique_token"] = unique_token

            return redirect("shared_album_detail", id=album.id)
    else:
        form = UserProfileForm()

    return render(request, "app/upload_selfie.html", {"form": form, "album": album, "business":business})


@login_required(login_url="login")
def business_settings(request):
    user = request.user
    business, created = Business.objects.get_or_create(user=user)

    if request.method == "POST":
        form = BusinessSettingsForm(request.POST, request.FILES, instance=business)
        if form.is_valid():
            form.save()
            return redirect("photographer_dashboard")  # Redirect to a success page
    else:
        form = BusinessSettingsForm(instance=business)

    return render(request, "app/business_settings.html", {"form": form})
