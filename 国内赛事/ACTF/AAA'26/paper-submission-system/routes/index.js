const registerHomeRoutes = require('./home');
const registerAuthRoutes = require('./auth');
const registerPaperRoutes = require('./papers');
const registerSearchRoutes = require('./search');
const registerReviewerRoutes = require('./reviewer');
const registerAdminRoutes = require('./admin');
const { render } = require('../lib/helpers');

function registerRoutes(app, auth) {
  registerHomeRoutes(app, auth);
  registerAuthRoutes(app, auth);
  registerPaperRoutes(app, auth);
  registerSearchRoutes(app, auth);
  registerReviewerRoutes(app, auth);
  registerAdminRoutes(app, auth);

  app.setNotFoundHandler((request, reply) => {
    return render(request, reply, 'error.ejs', { code: 404, message: 'The requested page does not exist.' });
  });
}

module.exports = {
  registerRoutes
};
