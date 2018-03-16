var request = require("request");

var data;

var options = { method: 'GET',
  url: 'https://fullprofile.atlassian.net/rest/api/2/search',
  qs: {
  	jql: 'project = ADS AND sprint = "A-Team" AND sprint in openSprints() AND sprint not in futureSprints()',
  	maxResults: 500,
  },
  headers: 
   { 'Postman-Token': 'bf2d79fc-8a6c-49ec-a85e-fd18c0310f9d',
     'Cache-Control': 'no-cache',
     Authorization: 'Basic dGltLnZhbi5lbGxlbWVldDpBZ3JpZGlnaXRhbDEhamlyYQ==' } };

function APIrequest(){
	request(options, function (error, response, body) {
	  if (error) throw new Error(error);
	  //console.log(body);
	  data = body;
	  console.log(body['total'])
	});
}

APIrequest();
//console.log(data);