//const Robot = require('../models/Robot');
//const fs = require('fs');

exports.getStatus = (req,res,next) => {
    res.status(200).json({robot: { statut : 'ONLINE', vitesse:75,batterie:50} });
};