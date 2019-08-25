from flask import Flask, jsonify, render_template
import ssl
app = Flask(__name__)

# for CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST') # Put any other methods you need here
    return response
@app.route('/')
def index():
    #return app.send_static_file('index.html')
    return render_template('index.html')


@app.route('/data')
def names():
    data = {"names": ["John", "Jacob", "Julie", "Jennifer"]}
    return jsonify(data)


#if __name__ == '__main__':
#    app.run()
if __name__ == '__main__':
     context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
     context.load_cert_chain("/opt/cert/nginx-selfsigned.crt", "/opt/cert/nginx-selfsigned.key")
     #context = ('/opt/cert/nginx-selfsigned.crt', '/opt/cert/nginx-selfsigned.key')#certificate and key files
     app.run(host='127.0.0.1', debug=False, ssl_context=context)
     #app.run(host='127.0.0.1', debug=True, ssl_context=context)
