'''
Web server to control DASI's FPI filterwheel operation and etalon temperature sensor.

Author. L Navarro
Date: 16 Sep 2021


At startup, filterwheel will execute homing position if [fw_start_homing] is True.
Inmediately after, it will locate to position indicated by [fw_startup_mode].

Global variables:
    fw_start_homing: [bool], indicates if homing is executed at startup
    
    fw_startup_mode: startup filter location after homing step.
                    None:    to avoid a default location
                    "blank": to locate into position 0
                    "green": to locate into position 1
                    "red":   to locate into position 2

Web requests:
    GET:
        url: [host_name]/log.txt
        return: serialized json of /home/pi/src/temperature.csv
                This file is saved by process /home/pi/src/temperaturesensor.py
    POST:
        data: dictionary with following keys,
                {"command":"filterwheel","status":""}, requests current filterwheel position. returns 0,1,2,3
                {"command":"filterwheel","position":"X"}, requests move filterwheel to position X. X can be 0,1,2,3
                {"command":"filterwheel","home":""}, requests homing sequence and lands filterwheel in position 0


'''

from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from filterwheel import FilterWheel
from urllib import parse

# Change this to your Raspberry Pi IP address
#host_name = 'raspberryfpi.local'
host_name = '0.0.0.0'
host_port = 80

#Global flag to enable/disable initial homing position
fw_startup_homing=True

#Change this to indicate position at startup i.e. position after homing. 
# blank for position 0
# green for position 1
# red   for position 2
# None  to avoid startup position
fw_startup_mode="red"


#Global variables/objects (not configurables)
LASTPOSITION=None
fw=None

def saveinlog(text,path="/home/pi/log/raspberryfpi_server.log"):
    h=open(path,'a')
    line="%s:: %s\n"%( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), text )
    h.write(line)
    h.close()

class FPIHandler(BaseHTTPRequestHandler):
    """ 
    A special implementation of BaseHTTPRequestHander for reading data 
    """
    def set_filterwheel_position(self,position):
        global LASTPOSITION
        global fw
        saveinlog("POSITION REQUESTED %i (OLD:%i)"%(position,LASTPOSITION))
        desired_pos=[fw.filter0_pos,fw.filter1_pos,fw.filter2_pos,fw.filter3_pos]
        fw.pos=LASTPOSITION
        fw.goto(desired_pos[position])
        LASTPOSITION=fw.pos
        saveinlog("SUCCESS")
    
    def get_filterwheel_position(self,):
        global fw
        desired_pos=[fw.filter0_pos,fw.filter1_pos,fw.filter2_pos,fw.filter3_pos]
        pos=desired_pos.index(fw.pos)
        saveinlog("CURRENT POSITION %i"%(pos))
        return pos

    def home_filterwheel(self,):
        global LASTPOSITION
        global fw
        saveinlog("REQUESTED HOMING SEQUENCE")
        if fw.pos in [0,fw.filter0_pos]:#get away from sensor if you are already there
            self.set_filterwheel_position(1)
        fw.home()
        LASTPOSITION=fw.pos
        saveinlog("SUCCESS REACHING HOME")
        self.set_filterwheel_position(0)

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _redirect(self, path):
        self.send_response(303)
        self.send_header('Content-type', 'text/html')
        self.send_header('Location', path)
        self.end_headers()

    def do_GET(self):
        self.do_HEAD()
        if 'log.txt' in self.path:
            h=open("/home/pi/src/temperature.csv","r")
            text=h.read()
            h.close()
            self.wfile.write(text.encode("utf-8"))
            saveinlog("log.txt dumped")

    def do_POST(self):
        # Get the post data
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode("utf-8")
        post_data=parse.parse_qs(post_data)
        if "command" in post_data.keys():
            command=post_data["command"][0]
            saveinlog("COMMAND %s just received with data"%(command))
            if command == "filterwheel":
                if "position" in post_data.keys():
                    position=int(post_data["position"][0])
                    self.set_filterwheel_position(position)
                    self.do_HEAD()
                elif "status" in post_data.keys():
                    self.do_HEAD()
                    pos=self.get_filterwheel_position()
                    text="%i"%pos
                    self.wfile.write(text.encode("utf-8"))
                elif "home" in post_data.keys():
                    self.home_filterwheel()
                    self.do_HEAD()

   #     self._redirect('/')


if __name__ == '__main__':

    if fw_startup_homing:
        saveinlog("Homing filterwheel")
        fw=FilterWheel()
        fw.home()
    
    saveinlog("Startup mode: %s"%(str(fw_startup_mode)))
    if fw_startup_mode is not None:
    
        if fw_startup_mode == 'blank':
            fw.goto(fw.filter0_pos)
        elif fw_startup_mode == 'green':
            fw.goto(fw.filter1_pos)
        elif fw_startup_mode == 'red':
            fw.goto(fw.filter2_pos)

        LASTPOSITION=fw.pos

    saveinlog("Running server on %s:%s" % (host_name, host_port))
    http_server = HTTPServer((host_name, host_port), FPIHandler)
    http_server.serve_forever()


