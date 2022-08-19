//const Robot = require('../models/Robot');
//const fs = require('fs');

const robot = {
    status : 'Online',
    vitesse:50,
    batterie:90,
    camera:'Offline',
    direction:'DOWN'
}
exports.getStatus = (req,res,next) => {
    res.status(200).json({robot: { status : robot.status, vitesse:robot.vitesse,batterie:robot.batterie,camera:robot.camera,direction:robot.direction} });
};

exports.handleCmd = (req,res,next) => {
    console.log(req.body.cmd)

    if(typeof req.body.cmd === 'number')
    {
        robot.vitesse = Math.round(req.body.cmd)
    }
    else
    {
        robot.direction = req.body.cmd
    }
    res.status(200).json({message:'SUCCES'});
};