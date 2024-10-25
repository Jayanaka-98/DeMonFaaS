# Backend

## Goal:
- One monolithic FASTAPI app that is connected to the database and can have apis attached but doesn't necessarily.
- Endpoints / groups of endpoints will have their own dockerfile that is for a serverless function
- if deployed serverlessly with the maximum modularity, the FASTAPI code will not be triggered at all and the request will be sent directly to the serverless function. Does this mean that we can keep the fastAPI image the same and just route differently in the openFaaS gateway? perhaps!

This repo will be the maximum amount modularity. 
ISSUE: if we can have any combination of modularity, there are too many images to create of the main app. Might have to dynamically create a new app