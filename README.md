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


# Plug-ins Architecture

In computing, a plug-in (or plugin, add-in, addin, add-on, or addon) is a software component that adds a specific feature to an existing computer program. When a program supports plug-ins, it enables customization.

voCAPTCHA is extensible - customer's are welcome to and encouraged to bring their own challenge generation solutions via the creation of a VoCaptchaPlugin.  

## Plugins

voCAPTCHA v2 is a Python application which means plugins are written in Python.  

New plugin's can be created by creating a new Python module in the plugins folder.  

```diff
.
├── Dockerfile
├── README.md
├── cloudbuild.yaml
├── poetry.lock
├── pyproject.toml
├── service
│   ├── __init__.py
│   ├── main.py
│   ├── plugins <- ! THIS IS THE PLUGINS FOLDER!
│   │   ├── add_numbers.py
│   │   ├── nato_alpha.py
│   │   └── sentences.py
│   ├── vocaptcha <- ! THIS IS THE VOCAPTCHA CORE FOLDER
│   │   ├── cache.py
│   │   ├── plugins.py <- THIS IS WHERE THE VoCaptchaPlugin base class lives!
│   │   └── server.py
│   └── vocaptcha.yaml
└── tests
    └── __init__.py
```

The module itself needs to (at a minimum) hold a class that sub-classes the VoCaptchaPlugin abstract base class located under the vocaptcha folder.  

Notice that CLASS attributes (MOUNT, TYPE, DOC, PARAMS) have been exposed for convenience.  

By using class attributes like this, the need to define an `__init__` method is circumvented; and anything that's exposed as a class attribute is and should be a constant within the plugin.   

```python
# service/plugins/my_plugin.py

from vocaptcha.plugins import VoCaptchaPlugin


class MyVeryOwnPlugin(VoCaptchaPlugin):

    # CLASS ATTRIBUTES
    MOUNT = "/my-very-own-plugin"
    TYPE = "custom-plugin"
    DOC = "custom-plugin"
    PARAMS = None

    ...
```

The MOUNT class attribute represents the root path of the plugin.  Given ```MOUNT="/coffee-types"```, the routes created would be `/coffee-types/generate` and `/coffee-types/verify`.  

The TYPE class attribute is used as metadata.  The virtual agent uses this to confirm that the challenge response and request type match - just as a security check.  

The DOC class attribute is responsible for mapping the Plugin's response and challenge materials from Firestore.  It represents the documents name.  

The PARAMS class attribute is optional.  PARAMS exposes parameters that may be tweaked, typically for challenge generation - but these PARAMS can be used within the generate and verify methods as well.  


The VoCaptchaPlugin base class requires you to implement two methods: `generate` and `verify`.  To work properly, the signature for those methods MUST be of this format:

```python
async def generate(self, webhook: WebhookRequest, templates=..., response=...):
    ...
```

Behind the scenes, the plugin base class stages some transformations, validations, and also instantiates objects (like the WebhookResponse object) so the user doesn't need to.  

The function should generate a challenge, update any templates with those challenge materials and return the response object (which is injected via the response key word argument at runtime.)

```python
async def generate(
    self, 
    webhook: WebhookRequest, 
    templates=..., 
    response=...
):
    # you can define other methods, too
    # Here, the challenge method is defined for challenge generation.
    challenge = self.challenge() 
    # Update the templates
    text = templates['generate']['text'].format(challenge=challenge)
    ssml = templates['generate']['ssml'].format(challenge=challenge)
    # Update the WebhookResponse object
    response.add_text_response(text)
    response.add_audio_text_response(ssml)
    response.add_session_params({
        "challenge": " ".join(words),
        "challenge-type": self.TYPE
    })
    # Return the response object.  
    return response
```

The verify method works in nearly the same way.  See the plugins folder for more examples.

The VoCaptchaPlugin class provides a couple of out-of-the-box helper methods that provide integration with the ResponseCache which keeps a copy of all VoCaptcha response materials in memory and in-sync with Firestore where those definitions live.

```python
    def get_challenges(self):
        """
            responsible for getting challenges from the cache.
        """
        document = self.cache.get(self.doc)
        challenges = document.get(CHALLENGES)
        if not challenges:
            raise NotImplementedError("No challenges found!  Please review.")
        return challenges

    def get_templates(self):
        """
            responsible for getting response templates from the cache.
        """
        document = self.cache.get(self.doc)
        templates = document.get(TEMPLATES)
        if not templates:
            raise NotImplementedError("No templates found!  Please review.")
        return templates
```

By using Firestore, the response messages and the challenge materials are fully decoupled from the application - and still keep the cache in sync with the source of truth.  This, in turn, allows customers to update the response and challenge materials in real-time without having to rebuild the application.

If voCAPTCHA v2 is up-and-running, you can change the format of the response message from within Firestore and you can also add more challenge materials dynamically by updating the document that contains that information.  

## The ResponseCache

The ResponseCache is a concurrency safe wrapper around Firestore's "watcher" method for queries, collections, and documents: `on_snapshot`, which starts listening for changes to the provided Firestore reference object on a separate background thread.  

When updates are detected, a mutex lock is used to prevent access - preventing the corruption of data in-transit.  

Changes don't happen frequently, but when they do, it's the ResponseCache's job to ensure that those changes are propagated in near real-time.  


## voCAPTCHA Config: vocaptcha.yaml

At this time, voCAPTCHA's plugin discovery and plugin registration is done manually via a configuration file which exposes a limited number of configuration options.

```yaml
plugins:
  - module: nato_alpha
    cls: NATOAlphaPlugin
  - module: sentences
    cls: SentencesPlugin
  - module: add_numbers
    cls: AddTwoNumbersPlugin
collection: vocaptcha-v3-plugins
pluginFolder: plugins
```

- plugins is a list of module and class pair maps
- collection is the name of the collection in Firestore that holds challenge and template materials
- pluginFolder is where the voCAPTCHA server process will look for the listed plugins.  This shouldn't need a change - but is included for advanced use.

Changes to this configuration WILL require a re-building of the container - but this makes sense.  if plugins are being added or removed, a rebuilding, for security reasons, should happen.

## ResponseCache Collection and Documents

Each Plugin has it's response and challenge materials de-coupled from it's definition.  The data lives inside a collection in Firestore and each plugin is represented by a Firestore Document that the Response Cache watches for changes.

The document is composed of two main sections:  challenges and templates.  Challenges hold challenge materials in whatever format you need (either a map or a list) and the response templates house the string templates used to generate responses.  

```json
{
    "challenges": [
        "Coffee is best served hot or cold",
        "The rain in Spain stays mainly in the plain",
        "It is time to pay taxes"
    ],
    "templates": [{
        "generate": {
            "text": "Please repeat the following sentence after me: {sentence}",
            "ssml": "Please repeat the following sentence after me: {sentence}"
            }
        },
        {
        "verify": {
            "text": "Cool.  We sent you the following sentence: {challenge} and you responded: {challenge_response}.  These two {match}.",
            "ssml": "Cool.  We sent you the following sentence: {challenge} and you responded: {challenge_response}.  These two {match}."
            }
        }
    ]
}
```

You can change the general format of the templates and where those parameters will go within the string 

```diff

- "Cool.  We sent you the following sentence: {challenge} and you responded: {challenge_response}.  These two {match}."
+ These two {match}.  Your response was: {challenge_response} and the challenge was: {challenge}.  "
```

The generate and verify methods are responsible for passing the parameters and filling the template out via the str.format python built-in.

# Key Technologies

voCAPTCHA v2 is built with Python using the following frameworks and technologies:

- Starlette: Starlette is a lightweight ASGI framework/toolkit, which is ideal for building async web services in Python.

- Pydantic: Data validation and settings management using python type annotations.  

- Google Cloud Firestore: Google Cloud's serverless real-time NoSQL Database with live synchronization capabilities.

- Google Cloud Build: Serverless CI/CD - perfect for using with GKE and Cloud Run.

- Google Cloud Run: Run highly scalable containerized applications on a fully managed serverless platform.
