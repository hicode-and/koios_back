const path = require('path');
//const Robot = require('../models/Robot');
//const fs = require('fs');
//var Gpio = require('onoff').Gpio; 
var Gpio = require('pigpio').Gpio;

var pwm2a = new Gpio(13,{mode:Gpio.OUTPUT})
var pwm2b = new Gpio(12,{mode:Gpio.OUTPUT})
var pwm1a = new Gpio(18,{mode:Gpio.OUTPUT})
var pwm1b = new Gpio(19,{mode:Gpio.OUTPUT})


var en1 = new Gpio(27,{mode:Gpio.OUTPUT})
var en2 = new Gpio(22,{mode:Gpio.OUTPUT})

/*
IO.setup(13,IO.OUT)
IO.setup(19,IO.OUT)
IO.setup(18,IO.OUT)
IO.setup(12,IO.OUT)

pwm1a = IO.PWM(18, 60)
pwm1b = IO.PWM(19, 60)

pwm2a = IO.PWM(13, 60)
pwm2b = IO.PWM(12, 60)*/


const robot = {
    status : 'Online',
    vitesse:50,
    batterie:90,
    camera:'Offline',
    direction:'DOWN',
    intern_vitesse:Math.round(50*2.55),
    intern_vitesse_reduced: Math.round(50*2.55*0.88),
    intern_vitesse_reduced_down: Math.round(50*2.55*0.95)
}
exports.getStatus = (req,res,next) => {
    res.status(200).json({robot: { status : robot.status, vitesse:robot.vitesse,batterie:robot.batterie,camera:robot.camera,direction:robot.direction} });
};

exports.handleCmd = (req,res,next) => {


    console.log(req.body.cmd)

    if(typeof req.body.cmd === 'number')
    {
        if(req.body.cmd != robot.vitesse)
        {
            robot.vitesse = Math.round(req.body.cmd)
            robot.intern_vitesse =  Math.round(robot.vitesse * 2.55)
            robot.intern_vitesse_reduced = Math.round(robot.intern_vitesse*0.88)
            robot.intern_vitesse_reduced_down = Math.round(robot.intern_vitesse*0.95)
            console.log(robot.intern_vitesse)

            if(robot.direction == "LEFT")
            {
                pwm2a.pwmWrite(robot.intern_vitesse);
                pwm2b.pwmWrite(robot.intern_vitesse);
            }
            else if(robot.direction == "RIGHT")
            {
                pwm1a.pwmWrite(robot.intern_vitesse);
                pwm1b.pwmWrite(robot.intern_vitesse);
            }
            else if(robot.direction == "UP")
            {
                pwm1b.pwmWrite(robot.intern_vitesse_reduced)
                pwm2b.pwmWrite(robot.intern_vitesse)
            }
            else if(robot.direction == "DOWN")
            {
                pwm1a.pwmWrite(robot.intern_vitesse_reduced_down)
                pwm2a.pwmWrite(robot.intern_vitesse)
            }
        }
    }
    else
    {
        if(req.body.cmd != robot.direction)
        {
            if(req.body.cmd=="LEFT")
            {
                console.log("LEFT")

                en1.digitalWrite(0);
                en2.digitalWrite(1);                

                pwm1a.pwmWrite(0);
                pwm1b.pwmWrite(0);

                pwm2a.pwmWrite(robot.intern_vitesse);
                pwm2b.pwmWrite(robot.intern_vitesse);
            }
            else if(req.body.cmd=="RIGHT")
            {
                console.log("RIGHT")

                en1.digitalWrite(1);
                en2.digitalWrite(0);                

                pwm1a.pwmWrite(robot.intern_vitesse);
                pwm1b.pwmWrite(robot.intern_vitesse);

                pwm2a.pwmWrite(0);
                pwm2b.pwmWrite(0);
            }
            else if(req.body.cmd=="UP")
            {
                console.log("UP")

                en2.digitalWrite(1);
                en1.digitalWrite(1);

                pwm1a.pwmWrite(0);
                pwm1b.pwmWrite(robot.intern_vitesse_reduced)

                pwm2a.pwmWrite(0);
                pwm2b.pwmWrite(robot.intern_vitesse)
            }
            else if(req.body.cmd=="DOWN")
            {
                console.log("DOWN")
                en1.digitalWrite(1);
                en2.digitalWrite(1);

                pwm1a.pwmWrite(robot.intern_vitesse_reduced_down)
                pwm1b.pwmWrite(0);

                pwm2a.pwmWrite(robot.intern_vitesse)
                pwm2b.pwmWrite(0);
            }
            else
            {
                en1.digitalWrite(0);
                en2.digitalWrite(0);                

                pwm1a.pwmWrite(0);
                pwm1b.pwmWrite(0);

                pwm2a.pwmWrite(0);
                pwm2b.pwmWrite(0);
            }
            robot.direction = req.body.cmd
        }
    }
    res.status(200).json({message:'SUCCES'});
    

};

exports.getPicture = (req,res,next) => {
    res.sendFile(path.join(__dirname + '../ressources/r2d2.jpg'));
};