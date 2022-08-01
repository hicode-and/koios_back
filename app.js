const express = require('express');
const mongoose = require('mongoose');
const app = express();
const path = require('path');

const robotRoutes = require('./routes/robot.js')
//const userRoutes = require('./routes/user.js');

/*mongoose.connect('mongodb+srv://pablo:aramir21@cluster0.zaoatsj.mongodb.net/?retryWrites=true&w=majority',
{
  useNewUrlParser:true,
  useUnifiedTopology: true})
  .then(()=> console.log('Connexion a mongoDB reussie !'))
  .catch(() => console.log('Connexion a mongoDB echouée!'));*/




app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content, Accept, Content-Type, Authorization');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS');
  next();
});

app.use(express.json());
app.use('/api/robot',robotRoutes)
//app.use('/api/auth', userRoutes);
//app.use('/images', express.static(path.join(__dirname, 'images')));
module.exports = app;