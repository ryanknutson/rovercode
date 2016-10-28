from flask import Flask, jsonify, Response, request, send_from_directory
from os import listdir
from os.path import isfile, join
import xml.etree.ElementTree
import Adafruit_GPIO.PWM as pwmLib

app = Flask(__name__)

pwm = pwmLib.get_platform_pwm(pwmtype="softpwm")

@app.route('/api/v1/blockdiagrams', methods=['GET'])
def get_block_diagrams():
    names = []
    for f in listdir('saved-bds'):
        if isfile(join('saved-bds', f)) and f.endswith('.xml'):
            names.append(xml.etree.ElementTree.parse(join('saved-bds', f)).getroot().find('designName').text)
    return jsonify(result=names)

@app.route('/api/v1/blockdiagrams', methods=['POST'])
def save_block_diagram():
    designName = request.form['designName'].replace(' ', '_').replace('.', '_')
    bdString = request.form['bdString']
    root = xml.etree.ElementTree.Element("root")

    xml.etree.ElementTree.SubElement(root, 'designName').text = designName
    xml.etree.ElementTree.SubElement(root, 'bd').text = bdString

    tree = xml.etree.ElementTree.ElementTree(root)
    tree.write('saved-bds/' + designName + '.xml')
    return ('', 200)

@app.route('/api/v1/blockdiagrams/<string:id>', methods=['GET'])
def get_block_diagram(id):
    id = id.replace(' ', '_').replace('.', '_')
    bd = [f for f in listdir('saved-bds') if isfile(join('saved-bds', f)) and id in f]
    with open(join('saved-bds',bd[0]), 'r') as content_file:
        content = content_file.read()
    return Response(content, mimetype='text/xml')

@app.route('/api/v1/download/<string:id>', methods = ['GET'])
def download_block_diagram(id):
    if isfile(join('saved-bds', id)):
        return send_from_directory('saved-bds', id, mimetype='text/xml', as_attachment=True)
    else:
        return ('', 404)

@app.route('/api/v1/upload', methods = ['POST'])
def upload_block_diagram():
    if 'fileToUpload' not in request.files:
        return ('', 400)
    file = request.files['fileToUpload']
    filename = file.filename.rsplit('.', 1)[0]
    suffix = 0
    # Check if there already is a design with this name
    while isfile(join('saved-bds', filename + '.xml')):
        suffix += 1
        # Append _# to the design name to make it unique
        if (suffix > 1):
            filename = filename.rsplit('_', 1)[0]
        filename += '_' + str(suffix)
    # Ensure that the design name is the same as the file name
    root = xml.etree.ElementTree.fromstring(file.read())
    designName = root.find('designName')
    designName.text = filename
    tree = xml.etree.ElementTree.ElementTree(root)
    tree.write(join('saved-bds', filename + '.xml'))
    return ('', 200)

@app.route('/api/v1/sendcommand', methods = ['POST'])
def send_command():
    run_command(request.form)
    return jsonify(request.form)

def init_rover_service():
    # set up motor pwm
    pwm.start("XIO-P0", 0);
    pwm.start("XIO-P1", 0);
    pwm.start("XIO-P6", 0);
    pwm.start("XIO-P7", 0);

    # test adapter
    if pwm.__class__.__name__ == 'DUMMY_PWM_Adapter':
        def mock_set_duty_cycle(pin, speed):
            print "Setting pin " + pin + " to speed " + str(speed)
        pwm.set_duty_cycle = mock_set_duty_cycle

def run_command(decoded):
    print decoded['command']
    if decoded['command'] == 'START_MOTOR':
        print decoded['pin']
        print decoded['speed']
        print "Starting motor"
        pwm.set_duty_cycle(decoded['pin'], float(decoded['speed']))
    elif decoded['command'] == 'STOP_MOTOR':
        print decoded['pin']
        print "Stopping motor"
        pwm.set_duty_cycle(decoded['pin'], 0)

if __name__ == '__main__':
    init_rover_service()
    app.run(host='0.0.0.0', debug=True)
