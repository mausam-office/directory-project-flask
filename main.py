'''Author: Mausam Rajbanshi (AI Developer)'''
# import aiofiles
import os

from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

from decouple import config


from utils.utils import fast_scandir, latest_version, allowed_file


app = Flask("Directory Management")


# static password stored in env file    #Technology@123
static_password = {'username':config('user_name'), 'password':config('password')}

# ROOT_DIR = os.path.join(os.path.abspath('.'), 'projects')
ROOT_DIR = os.path.join(os.path.dirname(__file__), 'projects')
os.makedirs(ROOT_DIR, exist_ok=True)

@app.get("/")
def home():
    return render_template('home.html')

@app.get("/login")
def login():
    return render_template('login.html')

@app.post("/dirManager")
def authenticated():
    username = request.form.get('username')
    password = request.form.get('password')
    if username == static_password["username"] and password == static_password["password"]:
        # authenticated
        # scans for directories in project directory
        directories = fast_scandir(ROOT_DIR)
        
        return render_template(
            'dirManager.html',
            directories=directories
        )
    else:
        # return "Username and password mismatch"
        return render_template(
            'redirect.html',
            url="/login"
        )

@app.post("/create")    
def create_dir():
    dirName = request.form.get('dirName')
    # create directory in reference to root dir 
    dir_to_create = os.path.join(ROOT_DIR, dirName)

    if os.path.exists(dir_to_create) and os.path.isdir(dir_to_create):
        msg = f"Project named `{dirName}` already exists."
    else:
        os.makedirs(dir_to_create, exist_ok=True)
        msg = f"Created directory `{dir_to_create}`."

    # scans for directories in project directory
    directories = fast_scandir(ROOT_DIR)
    return render_template(
            'dirManager.html',
            directories = directories, 
            created = msg
        )

@app.post("/upload")
def upload():
    selectDir = request.form.get('selectDir')
    if 'selectFile' not in request.files:
        return
    file = request.files['selectFile']
    if file and allowed_file(file.filename):
            filename = secure_filename(str(file.filename))   # extract filename from uploaded file
    # filename = secure_filename(file.filename)   
    
    update = None

    filepath = os.path.join(selectDir, filename)    # create filepath 

    # format filepath for version-control file `update.txt`
    filename_parts = filename.split('.')[0].split('_')
    txt_filename = filename_parts[0] + '.txt'
    txt_filepath = os.path.join(selectDir, txt_filename)

    # only upload when new version is available 
    if os.path.exists(txt_filepath) and os.path.isfile(txt_filepath):
        available_version = latest_version(txt_filepath)
        new_version = int(filename_parts[1][1:])
        update = True if new_version > available_version else False

    # also upload when there is no version
    paths = os.listdir(selectDir)
    paths = [path for path in paths if os.path.isfile(os.path.join(selectDir, path))]
    if not paths:
        update = True

    if update:
        # store the bin file 
        file.save(filepath)
        
        # update/create update.txt file
        with open(txt_filepath, 'w') as update_f:
            update_f.write(filename_parts[1])

        msg = f"Uploaded file `{filepath}`.\nUpdated file {txt_filepath}."
    else:
        msg = "Upload terminated due to lower or same version of uploaded file."

    # scans for directories in project directory
    directories = fast_scandir(ROOT_DIR)
    
    return render_template(
            'dirManager.html',
            directories=directories, 
            uploaded=msg
        )

@app.get("/version/<path:project_name>")
def get_version(project_name):
    '''Returns the latest version'''
    project_vc = os.path.join(ROOT_DIR, project_name, 'update.txt')

    if os.path.exists(project_vc) and os.path.isfile(project_vc):
        available_version = latest_version(project_vc)
        return {'version':available_version}
    else:
        return {'version':None}


# call http://127.0.0.1:8000/download/project_name/version
@app.get('/download/<path:project_name>/<version>')
def download(project_name, version):
    vc_filepath = os.path.join(ROOT_DIR, project_name, "update.txt")
    try:
        assert os.path.exists(vc_filepath)
        assert os.path.isfile(vc_filepath)
    except AssertionError as e:
        return {'msg':"Please check the project path."}
    
    try:
        assert version.isalnum()
        assert version.startswith('v')
        wanted_version = version[1:]
        assert wanted_version.isnumeric()
        wanted_version = int(wanted_version)
    except Exception as e:
        # print(f"{e = }")
        return {'Erorr':str(e)}
    
    project_dir = os.path.join(ROOT_DIR, project_name)
    filename = f'update_v{version}.bin'
    return send_from_directory(project_dir, filename)


# # @app.get('/download')     # call http://127.0.0.1:8000/download?project_name=d&version=v0
# @app.get('/download/{project_name}/{version}')      # call http://127.0.0.1:8000/download/project_name/version
# def download(project_name:str, version:str):
#     '''downloads project file for requested version'''
#     file_location = os.path.join(ROOT_DIR, project_name, "update.txt")

#     # update.txt filepath validation
#     try:
#         assert os.path.exists(file_location)
#         assert os.path.isfile(file_location)
#     except AssertionError as e:
#         return "Please check the project path."
    
#     # requested version validation
#     # wanted_version = version[1:] if version.isalnum() else version if version.isnumeric() else None
#     try:
#         assert version.isalnum()
#         assert version.startswith('v')
#         wanted_version = version[1:]
#         assert wanted_version.isnumeric()
#         wanted_version = int(wanted_version)
#     except Exception as e:
#         print(f"{e = }")
#         return 'Erorr occured: '+str(e)

#     # bin filename and filepath formation
#     file_name = f"update_v{wanted_version}.bin"
#     file_location = os.path.join(ROOT_DIR, project_name, file_name)

#     # download if filepath indicates file and it exists
#     if os.path.exists(file_location) and os.path.isfile(file_location):
#         return FileResponse(file_location, media_type='application/octet-stream', filename=file_name)
    
#     return "Requested file not available"

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')