var fs = require('fs');
var gulp = require('gulp');

gulp.task('copy_secrets', function(cb){
  fs.writeFile('packet/serviceAccountKey.json', process.env.FIREBASE_ADMIN_SDK, cb);
});