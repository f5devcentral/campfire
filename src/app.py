import argparse
import os
import json
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, Response, send_file
from werkzeug.utils import secure_filename
from flask import send_from_directory
from irulelogapi import flaminglog
from cairosvg import svg2png


UPLOAD_FOLDER = '/app'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','svg'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def webprint():
    return render_template('page.html') 

@app.route('/userdocs/')
def userdocs():
    return render_template('userdoc.html') 

@app.route('/faq/')
def faq():
    return render_template('faqpage.html') 

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/return-file/')
def return_file():
    path = "static/myflame1Combined.svg" 
    return send_file(path, as_attachment=True)

@app.route('/return-filepng/')
def return_filepng():
    path = "static/myflame1Combined.png" 
    return send_file(path, as_attachment=True)

@app.route('/return-filesep/')
def return_filesep():
    path = "static/myflame1Separate.svg" 
    return send_file(path, as_attachment=True)

@app.route('/return-fileseppng/')
def return_fileseppng():
    path = "static/myflame1Separate.png" 
    return send_file(path, as_attachment=True)

@app.route('/return-file2/')
def return_file2():
    path = "static/myflame2Combined.svg" 
    return send_file(path, as_attachment=True)

@app.route('/return-file2png/')
def return_file2png():
    path = "static/myflame2Combined.png" 
    return send_file(path, as_attachment=True)

@app.route('/return-file2sep/')
def return_file2sep():
    path = "static/myflame2Separate.svg" 
    return send_file(path, as_attachment=True)

@app.route('/return-file2seppng/')
def return_file2seppng():
    path = "static/myflame2Separate.png" 
    return send_file(path, as_attachment=True)

@app.route('/return-diff1/')
def return_diff1():
    path = "static/diff1.svg" 
    return send_file(path, as_attachment=True)

@app.route('/return-diff1png/')
def return_diff1png():
    path = "static/diff1.png" 
    return send_file(path, as_attachment=True)

@app.route('/return-diff2/')
def return_diff2():
    path = "static/diff2.svg" 
    return send_file(path, as_attachment=True)

@app.route('/return-diff2png/')
def return_diff2png():
    path = "static/diff2.png" 
    return send_file(path, as_attachment=True)

@app.route('/return-onlydiff/')
def return_onlydiff():
    path = "static/onlydiff.svg" 
    return send_file(path, as_attachment=True)

@app.route('/return-onlydiffpng/')
def return_onlydiffpng():
    path = "static/onlydiff.png" 
    return send_file(path, as_attachment=True)

@app.route('/make-new/')
def make_new(): 
    return redirect(url_for('webprint'))

 
@app.route('/', methods=['POST'])
def upload_file():
    flaminglog.cleanup()
    filename1 = "empty" 
    filename2 = "empty"
    filename3 = "empty"
    checked = request.form.getlist('mycheckbox')
    event = request.form.getlist('EVENT')
    irule = request.form.getlist('IRULE')
    flow = request.form.getlist('FLOW')
    remote = request.form.getlist('REMOTE')
    local = request.form.getlist('LOCAL')
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename1 = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename1))
        file = request.files['file2']
        if file.filename == '':
            flash('No selected file')
        if file and allowed_file(file.filename):
            filename2 = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename2))
        file = request.files['file3']
        if file.filename == '':
            flash('No selected file')
        if file and allowed_file(file.filename):
            filename3 = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename3))
        if not check_filter_inputtest(event):
            return render_template('page.html')
        return redirect(url_for('uploaded_file',filename1=filename1, filename2=filename2, filename3=filename3, checked=checked, event=event, irule=irule, flow=flow, remote=remote, local=local))



@app.route('/<filename1>/<filename2>/<filename3>/<checked>/<event>/<irule>/<flow>/<remote>/<local>')
def uploaded_file(filename1, filename2, filename3, checked, event, irule, flow, remote, local):
    if (filename1 != "empty") and ((filename2 != "empty") or (filename3 != "empty")):
        return redirect(url_for('upload_file'))
    if (filename1 == "empty") and ((filename2 == "empty") or (filename3 == "empty")):
        return redirect(url_for('upload_file'))
    fileDict = {
        'static/myflame1Combined.svg':None,
        'static/myflame1Separate.svg':None,
        'static/myflame2Combined.svg':None,
        'static/myflame2Separate.svg':None,
        'static/diff1.svg':None,
        'static/diff2.svg':None,
        'static/onlydiff.svg':None
    }
    errorMessage = ""
    exitcode = "0"
    namelist = "kyle"
    filtervaluedict = {'eventval':event,'irule':irule,'flow':flow,'remote':remote,'local':local}
    for key in filtervaluedict:
        if not check_filter_input(filtervaluedict[key]):
            return redirect(url_for('upload_file'))
    filtervaluedict = flaminglog.parse_filter_dict(filtervaluedict)
    if filename1 != "empty":
        name1, list1, errCode = flaminglog.make_json(filename1, checked)
        if(errCode == 0):
            filterList1 = flaminglog.run_multiple_filters(filtervaluedict, list1)
            exit1, fileDict = flaminglog.make_svg(filterList1)
            for key in fileDict:
                if fileDict[key] is not None:
                    flaminglog.svg_to_png(key, key[:-3]+"png")
        else:
            errorMessage = flaminglog.handle_error(errCode) + " Error in file: " + filename1
    else:
        name2, list2, errCode2 = flaminglog.make_json(filename2, checked)
        name3, list3, errCode3 = flaminglog.make_json(filename3, checked)
        if(errCode2 != 0):
            exitcode = errCode2
            errorMessage = flaminglog.handle_error(errCode2) + " Error in file: " + filename2
        elif(errCode3 != 0):
            exitcode = errCode3
            errorMessage = flaminglog.handle_error(errCode3) + " Error in file: " + filename3
        else:
            filterList2 = flaminglog.run_multiple_filters(filtervaluedict, list2)
            filterList3 = flaminglog.run_multiple_filters(filtervaluedict, list3)
            exitCodeDiff, fileDict = flaminglog.make_svg(filterList2, filterList3)
            exitcode = exitCodeDiff
            for key in fileDict:
                if fileDict[key] is not None:
                    flaminglog.svg_to_png(key, key[:-3]+"png")
    return render_template('resultspage.html', exitcode=exitcode, str1=fileDict['static/myflame1Combined.svg'], str2=fileDict['static/myflame1Separate.svg'], str3=fileDict['static/myflame2Combined.svg'], str4=fileDict['static/myflame2Separate.svg'],
					str5=fileDict['static/diff1.svg'], str6=fileDict['static/diff2.svg'], str7=fileDict['static/onlydiff.svg'], filename1=filename1, checked=checked, namelist=namelist, event=event, irule=irule, flow=flow,
					remote=remote, local=local, filters=filtervaluedict, filename2=filename2, filename3=filename3, errorMessage=errorMessage)


def check_filter_input(inputStr):
    badChars = ['(', ')', '&', '|', '^', '=']
    for char in badChars:
        if(char in inputStr):
            return False
    return True

def check_filter_inputtest(inputStr):
    if('/' in inputStr):
        return False
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='cdvm/runner factory')
    parser.add_argument('-a', '--address', default='0.0.0.0', help="address for server to bind to")
    parser.add_argument('-p', '--port', default='5002', help="port for server to bind to")

    args = parser.parse_args()
    app.secret_key = os.urandom(12)
    app.run(host=args.address, port=args.port, ssl_context=('cert.pem', 'key.pem'), debug=True)

