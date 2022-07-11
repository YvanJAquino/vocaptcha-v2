# voCAPTCHA v2

voCAPTCHA secures call centers by utilizing adaptive challenges to keep bots and auto-dialers from engaging in abusive activities using publicly available phone numbers. voCAPTCHA provides legitimate callers access to call center services after they successfully complete a randomly generated challenge. 


# Key Benefits

- Secure contact centers against malicious activities that utilize bots and auto dialers

- Improve customer experience by reducing hold times

- Easy to deploy as a flow in Dialogflow CX.

- Utilize provided analytics to identify phone numbers generating malicious calls.

- Reduce call volumes by eliminating robocall activity

# voCAPTCHA Fulfillment


The ADDF Fulfillment Layer  is a containerized stateless JSON web-service API.  It consists of 3 main components:  the server, plugins, and the response cache.  

The server’s role is to provide an API surface to webhook targets for the Dialogflow CX virtual agent.  It dynamically generates API endpoint paths (“challenge-type/generate, “challenge-type/verify”) based on registered plugins which define how to generate and verify challenges.    

ADDF Plugins hold the logic of the ADDF.   

The final piece of the ADDF is the response cache which is responsible for keeping an up-to-date representation of data used in and by the challenge generation and challenge verification processes. 

## voCAPTCHA Server


The server is responsible for delivering the API surface, the endpoints and paths that provide fulfillment to the ADDF Agent.  
It is responsible for discovering and registering plugins in addition to API endpoint route creation.  The server can run anywhere where containers are accepted such as on a VM running Container Optimized OS, a Kubernetes cluster, or even on a containers-as-a-service like Cloud Run.  
The ADDF server is stateless and can be run in a just-in-time fashion - it can be an ephemeral resource as opposed to a static, fixed one.  


## voCAPTCHA Plugins


Plugins define how a challenge is generated - and how that challenge is verified.  Plugins are based on a template, an abstract base class, which requires that both the challenge generation (generate) and the challenge verification (verify) methods are implemented - the Plugin’s base class takes care of the rest such as path generation and integration with the response cache.

Using a plugins based architecture allows the Fulfillment Layer to be user extensible.  Developers can write their own plugins in standard python, integrate data from any accessible data source, and the ADDF server will create unique endpoint paths for those plugin challenge and verification processes.   


## voCAPTCHA Response Cache


The response cache is responsible for managing the state of response materials.  Its process runs on a separate thread, listening for and making updates in real time.  It is safe for concurrent use.  The architectural decision to use an in-memory cache has a number of benefits:

- It de-couples “response” materials and data from the container.  When the customer needs to update a list of sentences used in challenge generation, they don’t need to ‘rebuild a container’ or re-release a new service.  Instead, they can update those definitions via a database (Firestore in this case) which provides real time updates, allowing the response cache to update itself as well for any running instances. 
- Consequently, keeping an in-memory representation of “response” materials allows ADDF Server to reduce the number of calls made to the data provider as well.  If no updates are made only one API call is made to the database during initialization.  

- It reduces the amount of round-trip latency between the Conversational Layer and the Fulfillment Layer.  No extra web service calls are made - the data is local to the ADDF server instance immediately - saving 15 milliseconds per interaction on average. 

# Key Technologies

voCAPTCHA v2 is built with Python using the following open source frameworks:

- Starlette: Starlette is a lightweight ASGI framework/toolkit, which is ideal for building async web services in Python.

- Pydantic: Data validation and settings management using python type annotations.  
