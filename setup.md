Using the Facebook Javascript SDK and jQuery to Create User Accounts with a Flask App
=====================================================================================

Getting Started with [developers.facebook.com](https://developers.facebook.com/)
--------------------------------------------------------------------------------

To work with any of the Facebook APIs, you need to be a Facebook developer. Just go to [developers.facebook.com](https://developers.facebook.com/) and sign up with your Facebook account. Once you're signed in, click on Apps and create a new app. In order to actually communicate with the app, you will need to register the app with a domain name where the app will live. One option for this is to use (heroku)[http://www.heroku.com/], although I used AWS on a subdomain of my existing domain. The repo in it's current state isn't set up for heroku, and may require a few changes to run there.

Using the Facebook JavaScript SDK
---------------------------------

I should first point out that Facebook has [fantastic documentation](https://developers.facebook.com/docs/howtos/login/getting-started/) for using this SDK. This section is mostly the same as the their content, with a few Flask specific things.

We start by inserting the JavaScript SDK initialization snippet after the opening of the `<body>` tag in `layout.html` and `index.html`. I put

    <div id="fb-root"></div>

in `layout.html` and then

    <script>
      // Additional JS functions here
      window.fbAsyncInit = function() {
        FB.init({
          appId      : 'YOUR_APP_ID', // App ID
          channelUrl : '//WWW.YOUR_DOMAIN.COM/channel.html', // Channel File
          status     : true, // check login status
          cookie     : true, // enable cookies to allow the server to access the session
          xfbml      : true  // parse XFBML
        });
        // Additional init code here
      };
      // Load the SDK Asynchronously
      (function(d){
         var js, id = 'facebook-jssdk', ref = d.getElementsByTagName('script')[0];
         if (d.getElementById(id)) {return;}
         js = d.createElement('script'); js.id = id; js.async = true;
         js.src = "//connect.facebook.net/en_US/all.js";
         ref.parentNode.insertBefore(js, ref);
       }(document));
    </script>

in a block called `facebook_js` in `index.html`, which extends `layout.hmtl`. I imagine some of the logic that we are going to build out will vary from page to page, hence making it specific to the `index.html` page, rather than in ever page that extends `layout.html`.

You will need to make two changes specific to your app: the `appId` and `channelUrl`. I hard coded the `channelUrl` to an absolute url, `http://my.app.com/channel` (but there are probably better ways to do this). I also added a route in the flask app. In `__init__.py`, add

    @app.route('/channel')
    def channel():
      return render_template('channel.html')

and in `templates/` add a file called `channel.html` with just

    <script src="//connect.facebook.net/en_US/all.js"></script>

in it.  Now we are set up to interface with Facebook. We now will need to check if the user is logged into Facebook and has authorized our app. In the above code block `facebook_js`, add the following within the `window.fbAsyncInit` function declaration (where we have `// Additional init code here`):

    FB.getLoginStatus(function(response) {
      if (response.status === 'connected') {
        // connected
      } else if (response.status === 'not_authorized') {
        // not_authorized
      } else {
        // not_logged_in
      }
     });

Right now, this code doesn't actually do anything, but we can now define different actions depending upon three cases: users is logged in to Facebook and has authorized your app, user is logged in to Facebook but not authorized your app, or user is not logged in to Facebook (and hence authorization is unknown).

Six Cases
---------

At this point we will introduce the concept of the app user as well. The idea here is that we will want to store the `facebook_id` server side so that we can poll their account info with another part of the application (or another process altogether). After we create or get the user, we will store the user object in the `session` variable. Now, when a user comes to our site, this will double the number of possible cases to 6:

1. App user is logged in AND user is logged into Facebook and has authorized your app
2. App user is logged in AND user is logged into Facebook but not authorized your app
3. App user is logged in AND user is not logged into Facebook (and hence authorization is unknown)
4. App user is not logged in AND user is logged into Facebook and has authorized your app
5. App user is not logged in AND user is logged into Facebook but not authorized your app
6. App user is not logged in AND user is not logged into Facebook (and hence authorization is unknown)

To handle these cases, we will render the JavaScript in the template differently depending upon if the user object exists:

    {% if user %}
    FB.getLoginStatus(function(response) {
      if (response.status === 'connected') {
       //user logged in and connected to facebook. case 1.
       console.log('user logged in and connected to facebook')
      } else if (response.status === 'not_authorized') {
       //user logged in but app not_authorized on facebook. case 2.
       console.log('user logged in but app not_authorized on facebook')
      } else {
       //user logged in but app not_logged_in to facebook. case 3.
       console.log('user logged in but app not_logged_in to facebook')
      }
    });
    {% else %}
    FB.getLoginStatus(function(response) {
      if (response.status === 'connected') {
        // user not logged in but connected to facebook. case 4.
        console.log('user not logged in but connected to facebook')
      } else if (response.status === 'not_authorized') {
        // user not logged in but app not_authorized on facebook. case 5. 
        console.log('user not logged in but app not_authorized on facebook')
      } else {
        // user not logged in and not_logged_in to facebook. case 6.
        console.log('user not logged in and not_logged_in to facebook')
      }
    });      
    {% endif %}

Again, this code doesn't actually do anything, but just sets us up to define what happens in each of these cases. To handle most of these cases, I used modals, provided by [Foundation 3](http://foundation.zurb.com/docs/reveal.php). Foundation is much like Twitter Bootstrap, but I found it to be more awesome. (I just came upon it, you'll note that my [Fractal Stock Game](http://skien.cc/fractal_game/random) was built with Twitter Bootstrap).

So now let's go through these case by case. In our first case, if the user is logged in on our site, as well as Facebook and authorized our app, we really don't need to do anything. This is what we want. So we don't need to do anything here. The next two cases assume that the user already exists on the app side, and has either removed the access to the Facebook app, or is not currently logged into Facebook. The fourth case assumes the user has authorized our app, is currently logged into Facebook, but not our app. We will come back to these cases.

Let's skip to the case where the user is a new user and has yet to authorize our app. We will either get case 5 or 6, depending upon if the user is currently signed into Facebook. Either way, we will want to prompt the user to login to Facebook (if needed) and authorize our app. This is done by calling the following function from the Facebook JavaScript SDK:

    FB.login(function(response) {
        if (response.authResponse) {
            // connected
            console.log('login successful')
        } else {
            // cancelled
            console.log('login failed ')
        }
    });

Now, this produces a pop-up from Facebook to allow the user to login (if needed) and then authorize the app. Most browsers will block popups like this if they are generated directly upon the page load, so it's better to attach this call to a user action, like clicking a button. So in the body of `index.html`, I created a modal with the following:

    <div id="login_modal" class="reveal-modal">
      <h2> Welcome to creeper! </h2>
      <p>
        Creeper requires you to login through your Facebook account.
      </p>
        <a href="#" id="facebook_login" class="button"> Get started. Login with Facebook. </a>
      </p>
    </div>

We want this modal to appear in cases 5 and 6, and we want to attach the `FB.login()` function to the button in the modal. To accomplish the first, we add following to cases 5 and 6 in the `FB.getLoginStatus()` functions:

    $("#login_modal").reveal();

It's important to note that the following is called before this chunk of Facebook JavaScript as this action above requires jQuery:

    <script src={{ url_for("static", filename="javascripts/jquery.js") }}></script>
    <script src={{ url_for("static", filename="javascripts/foundation.min.js") }}></script>
    <script src={{ url_for("static", filename="javascripts/app.js") }}></script>

Now, we can attach the `FB.login()` function to the button in the modal using jQuery as well: 

    $(function(){
      $('a#facebook_login').bind('click', function () {
          FB.login(function(response) {
              if (response.authResponse) {
                  // connected
                  console.log('login successful')
              } else {
                  // cancelled
                  console.log('login failed ')
              }
          });
          return false;
        });
      });

To deal with cases 2 and 3, we include the following 2 modals:

    <div id="user_no_facebook_auth_modal" class="reveal-modal">
      <h2> Whoops! </h2>
      <p>
        It seems that creeper isn't authorized on your Facebook account anymore.
      </p>
        <a href="#" id="facebook_login" class="button"> Reconnect to Facebook. </a>
      </p>
    </div>  

    <div id="user_no_facebook_login_modal" class="reveal-modal">
      <h2> Whoops! </h2>
      <p>
        It seems that you aren't logged into Facebook currently. Creeper works closely with 
        your Facebook account.
      </p>
        <a href="#" id="facebook_login" class="button"> Login to Facebook. </a>
      </p>
    </div>

and attach to case 2 with:

    $("#user_no_facebook_auth_modal").reveal();

and attach to case 3 with:

    $("#user_no_facebook_login_modal").reveal();

Since the `<a>` tags all have `id="facebook_login"`, so the `FB.login` function is attached to these buttons as well automatically.

The final case, case 4, is fairly simple. The user is logged into Facebook and authorized our app, so we just need to get that user object.

Creating and Getting the App User Object
----------------------------------------

So far we've only considered if the user object exists, but we haven't talked about creating and fetching it from the Flask app. Luckily we can pass data from the JavaScript response to the Flask app using jQuery. To do this, we make a JavaScript function `get_user()`:

    function get_user() {
        FB.api('/me', function(response) {
          $.getJSON($SCRIPT_ROOT + '/_get_facebook_login', 
                    { facebook_id: response.id, name: response.name },
                    function(data) {
                      console.log(data);
                      location.reload(true);
                    });
        });
    }

In a basic set up, `$SCRITP_ROOT` will be an empty string, however the [Flask docs](http://flask.pocoo.org/docs/patterns/jquery/) recommends using it and setting it to:

    <script type=text/javascript>
      $SCRIPT_ROOT = {{ request.script_root|tojson|safe }};
    </script>

This must be set before it's reference, obviously.

The `$.getJSON()` function takes a url, an object, _data_, and a function, _func_. The function makes a GET request to the url with the contents of the data object as query parameters. Once it gets a response, it calls _func_ with the response value as an argument.

Now, on the Flask app, we render `index.html` at `/` with:

    @app.route('/')
    def landing():
      return render_template('index.html', user=session.get('user', None))

This is going to pass a `user=None` until the user is set. So let's create the user.  First, let's define the `Users` class:

    class Users(db.Model):
      id = db.Column(db.Integer, primary_key=True)
      facebook_id = db.Column(db.Integer)
      name = db.Column(db.String(50))
    
      def __init__(self,facebook_id, name):
        self.facebook_id = facebook_id
        self.name = name

I put this in a separate `models.py`, but it can also go in `__init__.py` after the app is defined. Now, at `/_get_facebook_login` we attach:

    @app.route('/_get_facebook_login')
    def get_facebook_login():
      facebook_id = request.args.get('facebook_id', False, type=int)
      name = request.args.get('name', '', type=str)
      if facebook_id:
        user = Users.query.filter_by(facebook_id=facebook_id).first()
        if not user:
          user = Users(facebook_id,name)
          db.session.add(user)
          db.session.commit()
        session['user'] = user
      return jsonify(result=1)

This function looks for `facebook_id` and `name` from the request sent by `$.getJSON()` function. If we don't get the `facebook_id` then it skips getting the user and just returns `{"result":"1"}`. If we do, we first try to get a user from our database with that `facebook_id`, and if there is none, we create the user and commit it to the database. Either way, we add the user to the session. We could return a different value showing we now have the user, but we don't do anything with that data in the JavaScript. Now that the session has a user object, by returning a result, _func_ in `$.getJSON()` gets called. This triggers `location.reload(true);`, which reloads the page.

The final thing we need to do is drop in `get_user()` in a few places. In the end, the `FB.login()` call will look like:

    $(function(){
      $('a#facebook_login').bind('click', function () {
        FB.login(function(response) {
          if (response.authResponse) {
            // connected
            console.log('login successful')
            get_user()
          } else {
            // cancelled
            console.log('login failed ')
          }
        });
    return false;
      });
    });

and our `FB.getLoginStatus()` call will look like:

    {% if user %}
       FB.getLoginStatus(function(response) {
         if (response.status === 'connected') {
           //user logged in and connected to facebook
           console.log('user logged in and connected to facebook')
         } else if (response.status === 'not_authorized') {
           //user logged in but app not_authorized on facebook
           console.log('user logged in but app not_authorized on facebook')
           $("#user_no_facebook_auth_modal").reveal();
         } else {
           //user logged in but app not_logged_in to facebook
           console.log('user logged in but app not_logged_in to facebook')
           $("#user_no_facebook_login_modal").reveal();
         }
        }); 
      {% else %}
      FB.getLoginStatus(function(response) {
        if (response.status === 'connected') {
          // connected
          console.log('connected')
          $("#no_user_facebook_modal").reveal()
          get_user()
        } else if (response.status === 'not_authorized') {
          // not_authorized
          console.log('not authorized')
          $("#login_modal").reveal();
        } else {
          // not_logged_in
          console.log('not logged in')
          $("#login_modal").reveal();
        }
       });      
    {% endif %}










