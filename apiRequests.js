var request = require("request");

var options = { method: 'GET',
  url: 'https://fullprofile.atlassian.net/rest/api/2/search',
  qs: { jql: 'project=ADS+AND+sprint=%22A-Team%22+AND+sprint+in+openSprints%28%29+AND+sprint+not+in+futureSprints%28%29' },
  headers: 
   { 'Postman-Token': 'd56ae38d-3ecd-4de6-adfe-59b0b0844f57',
     'Cache-Control': 'no-cache',
     Authorization: 'Basic dGltLnZhbi5lbGxlbWVldDpBZ3JpZGlnaXRhbDEhamlyYQ==' } };

request(options, function (error, response, body) {
  if (error) throw new Error(error);

  console.log(body);
});
