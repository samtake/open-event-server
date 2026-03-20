import uuid

from flask import Blueprint, abort, jsonify, make_response, request
from flask_jwt_extended import jwt_required

from app.api.helpers.files import uploaded_file, uploaded_image
from app.api.helpers.storage import UPLOAD_PATHS, upload, upload_local

# 上传相关路由蓝图
upload_routes = Blueprint('upload', __name__, url_prefix='/v1/upload')


@upload_routes.route('/image', methods=['POST'])
@jwt_required
def upload_image():
    """上传图片"""
    # 获取图片数据
    image = request.json['data']
    # 获取扩展名
    extension = '.{}'.format(image.split(";")[0].split("/")[1])
    # 处理图片
    image_file = uploaded_image(extension=extension, file_content=image)
    # 检查是否强制本地上传
    force_local = request.args.get('force_local', 'false')
    if force_local == 'true':
        # 本地上传
        image_url = upload_local(
            image_file, UPLOAD_PATHS['temp']['image'].format(uuid=uuid.uuid4())
        )
    else:
        # 远程上传
        image_url = upload(
            image_file, UPLOAD_PATHS['temp']['image'].format(uuid=uuid.uuid4())
        )
    return jsonify({"url": image_url})


@upload_routes.route('/files', methods=['POST'])
@jwt_required
def upload_file():
    force_local = request.args.get('force_local', 'false')
    if 'file' in request.files:
        files = request.files['file']
        file_uploaded = uploaded_file(files=files)
        if force_local == 'true':
            files_url = upload_local(
                file_uploaded, UPLOAD_PATHS['temp']['event'].format(uuid=uuid.uuid4())
            )
        else:
            files_url = upload(
                file_uploaded, UPLOAD_PATHS['temp']['event'].format(uuid=uuid.uuid4())
            )
    elif 'files[]' in request.files:
        files = request.files.getlist('files[]')
        files_uploaded = uploaded_file(files=files, multiple=True)
        files_url = []
        for file_uploaded in files_uploaded:
            if force_local == 'true':
                files_url.append(
                    upload_local(
                        file_uploaded,
                        UPLOAD_PATHS['temp']['event'].format(uuid=uuid.uuid4()),
                    )
                )
            else:
                files_url.append(
                    upload(
                        file_uploaded,
                        UPLOAD_PATHS['temp']['event'].format(uuid=uuid.uuid4()),
                    )
                )
    else:
        abort(make_response(jsonify(error="Bad Request"), 400))

    return jsonify({"url": files_url})
