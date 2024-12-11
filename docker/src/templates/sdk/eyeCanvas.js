
const cursor = document.createElement('div');
cursor.setAttribute('id','cursor')
cursor.style.zIndex = 2000;
document.body.appendChild(cursor);

const calib_cursor = document.createElement('div');
calib_cursor.setAttribute('id','calib_cursor')
calib_cursor.style.zIndex = 2000;
document.body.appendChild(calib_cursor);

let overlayCanvas = null;
var calibration_counter = 0;
var calibration_points = 16;
var calibration_point = {'x':0, 'y':0};
var point = {'x':0, 'y':0};

function getUnixTimestamp(){
    return Math.floor(Date.now() / 1000);
}

var timestamp = getUnixTimestamp();

function createVideoElement(){
    let video = document.createElement("video");
    video.id = "localVideo";
    // video.width = 360;
    // video.height = 240;
    video.autoplay = true;
    video.muted = true;
    video.hidden = true;
    video.style.width = "auto";
    video.style.height = "auto";
    return video;
}

function createOverlayCanvas(){
    // Send each frame to the server
    let overlayCanvas = document.createElement('canvas');
    // Style the canvas to cover the entire viewport
    overlayCanvas.id = "overlayCanvas"
    overlayCanvas.style.position = 'fixed';
    overlayCanvas.style.top = 0;
    overlayCanvas.style.left = 0;
    overlayCanvas.style.width = '100vw';
    overlayCanvas.style.height = '100vh';
    overlayCanvas.style.zIndex = 1500;
    
    overlayCanvas.width = window.innerWidth;
    overlayCanvas.height = window.innerHeight;
    document.body.appendChild(overlayCanvas);

    const ctx = overlayCanvas.getContext('2d');
    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.fillRect(0, 0, overlayCanvas.width, overlayCanvas.height);
    return overlayCanvas;
}

function disableOverlayCanvas(){
    // Send each frame to the server
    overlayCanvas.remove();
    // const ctx = overlayCanvas.getContext('2d');
    // ctx.fillStyle = 'rgba(0, 0, 0, 0.0)';
    // ctx.fillRect(0, 0, overlayCanvas.width, overlayCanvas.height);
}

// Store original cursor styles
const originalCursorStyle = {
    background: cursor.style.background,
    border: cursor.style.border
};

const originalCalibCursorStyle = {
    background: calib_cursor.style.background,
    border: calib_cursor.style.border
};


function restoreOriginalCursors() {
    cursor.style.background = originalCursorStyle.background;
    cursor.style.border = originalCursorStyle.border;
}

function enableTransparentCursors(){
    // cursor.style.background = 'transparent';
    // cursor.style.border = 'transparent';
    calib_cursor.style.background = 'transparent';
    calib_cursor.style.border = 'transparent';
}

function createTransportCanvas(){
    // Send each frame to the server
    let trasnportCanvas = document.createElement('canvas');
    trasnportCanvas.width = 640;
    trasnportCanvas.height = 360;
    // return trasnportCanvas.getContext('2d');
    return trasnportCanvas;
}

const video = createVideoElement();
// Append the video element to the body or any other container
document.body.appendChild(video);
// Create transport view for changing video frame into sendable item
const trasnportCanvas = createTransportCanvas();

const socket = io('/engine/socket.io', { path: '/engine/socket.io' });  // This should match the namespace

navigator.mediaDevices.getUserMedia({ video: true })
.then(function (stream){    
    startVideoPlayer(video,stream);
    // start sending loop
    sendFrame();
}).catch(function(error){
    console.error('Error accessing the camera and microphone:', error);
});


function calibrated(){
    return calibration_counter > calibration_points
}

function update_calibrate_point(x,y)
{
    if(!calibrated() && (x !=  calibration_point.x || y != calibration_point.y))
    {
        calibration_point.x = x;
        calibration_point.y = y;
        calibration_counter +=1;
    }
}

function update_point(x,y)
{
    display_width  = document.body.clientWidth  - 100;
    display_height = document.body.clientHeight - 100;

    point.x = x < display_width? x : display_width;
    point.y = y < display_height? y : display_height;
    point.x = x > 0? x : 0;
    point.y = y > 0? y : 0;
}

function sendFrame(){
    // Flip the image horizontally

    if(!calibrated() && overlayCanvas == null)
    {
        overlayCanvas = createOverlayCanvas();
    }
    else if(calibrated() && overlayCanvas != null)
    {
        enableTransparentCursors();
        disableOverlayCanvas();
        overlayCanvas == null;
    }

    var trasnportContext = trasnportCanvas.getContext('2d');
    trasnportContext.drawImage(video, 0, 0, trasnportCanvas.width, trasnportCanvas.height);
    const imageData = trasnportCanvas.toDataURL('image/jpeg', 0.8); // Convert frame to base64
    display_width  = document.body.clientWidth  - 75,
    display_height = document.body.clientHeight - 75,

    console.log("Display width and length",
        display_width  = document.body.clientWidth  - 75,
        display_height = document.body.clientHeight - 75,
    )

    socket.emit('msg_data', {
        "height"    : display_height, 
        "width"     : display_width,
        "image"     : imageData ,
        "calibrate" : !calibrated(),
        "timestamp" : getUnixTimestamp(),
        "unique_id" : "{{ unique_id }}",
    });
}


function startVideoPlayer(video,stream)
{
    // Display the local video stream
    video.srcObject = stream;
    video.play();
}

socket.on('connect', function() {
    console.log('Connected to server');
    // Send data to the server on connect
    socket.emit('on_connect', {"unique_id" : "{{ unique_id }}"});
});

socket.on('rsp', (data) => {
    update_calibrate_point(data["c_x"],data["c_y"])
    update_point(data["x"],data["y"])
    cursor.style.left = `${point.x}px`;
    cursor.style.top = `${point.y}px`;
    console.log(data["radius"]);
    calib_cursor.style.width = data["radius"];
    calib_cursor.style.height = data["radius"];
    calib_cursor.style.left = `${calibration_point.x - 100}px`;
    calib_cursor.style.top = `${calibration_point.y - 100}px`;
    //code before the pause
    sendFrame();
}); 

