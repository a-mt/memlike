## Categories

Retrieve Memrise's tree of categories and translations:

``` js
// https://www.memrise.com/course/create/

var opts       = document.querySelector('select[name="target"]').children,
    categories = [],
    names      = {};

for(var i=0; i<opts.length; i++) {
  var opt = opts[i];
  if(!opt.value) {
    continue;
  }
  var name = opt.innerHTML;
  categories.push({
    id  : opt.value,
    lvl : (name.match(/&nbsp;/g) || []).length / 4
  });
  names[""+opt.value] = name.replace(/&nbsp;/g, '').trim();
};

copy(names);
```

Build the tree:

``` js
function to_tree(lvl) {
  var tree    = [],
      cat     = false,
      lastCat = false;

  while(categories.length) {
    var cat = categories[0];

    if(cat.lvl == lvl) {
      categories.shift();
      delete cat.lvl;
      tree.push(cat);

      lastCat = cat;

    } else if(cat.lvl > lvl) {
      lastCat.children = to_tree(cat.lvl);

    } else {
      break;
    }
  }
  return tree;
}

var tree = to_tree(0);
copy(tree);
```

Retrieve categories' codes:

``` js
// https://www.memrise.com/fr/courses/french/

var list  = document.querySelectorAll('li[data-category-id]'),
    categories_code = {};

for(var i=0; i<list.length; i++) {
    var li   = list[i],
        id   = li.getAttribute("data-category-id"),
        code = li.firstElementChild.getAttribute("href")
                 .replace(/\/$/, '').split('/').pop();

    categories_code[code] = id;
}
copy(categories_code);
```

Add code to categories:

``` js
var id2code = Object.keys(categories_code).reduce(function(obj,key){
   obj[ categories_code[key] ] = key;
   return obj;
},{});

function parse(children) {
  for(var i=0; i<children.length; i++) {
    var item = children[i];

    if(typeof id2code[item['id']] != "undefined") {
      item.code = id2code[item['id']];
    }
    if(item.children) {
      parse(item.children);
    }
  }
}
parse(categories);
copy(categories);
```

## Languages

``` js
// https://www.memrise.com/courses/english/

var ul = document.querySelector(".filter-source .dropdown-menu"),
    lang = {};

for(var i=0; i<ul.children.length; i++) {
    var a    = ul.children[i].firstElementChild,
        code = a.getAttribute("href").replace(/\/$/, '').split('/').pop(),
        name = a.innerText.trim();

    lang[code] = name;
}
copy(lang);
```

## Tests

Course with
* multiple images: /course/399843/human-neuroanatomy/2/
* audio: /course/365747/80-operas-with-audio/1/
* video: /course/1096771/anglais-britannique-1/
* no level: /course/233943/livre-1001-phrases-pour-parler-allemand/

## Login

GET https://app.memrise.com/v1.17/web/ensure_csrf
Request Header
    Cookie
    	ajs_anonymous_id=%2237e4a393-1545-4bbc-bc6d-01e0e3dfdc5a%22;
    	G_ENABLED_IDPS=google;
    	ab.storage.sessionId.81b5a720-d869-44a3-b051-fbf0e709467a=%7B%22g%22%3A%22a9b80de1-19c8-9370-7d7a-9e48ad7cc2de%22%2C%22e%22%3A1609413161834%2C%22c%22%3A1609413131813%2C%22l%22%3A1609413131834%7D;
    	ab.storage.deviceId.81b5a720-d869-44a3-b051-fbf0e709467a=%7B%22g%22%3A%2245f543bb-c766-07bb-169b-9d9a241a7399%22%2C%22c%22%3A1609413131815%2C%22l%22%3A1609413131815%7D;
    	_gcl_au=1.1.1566296011.1609413132;
    	__stripe_mid=7954b20f-3ea1-430a-911f-0b588469e247a4a44c;
    	__stripe_sid=d7d1b258-fad7-41ed-9659-43d87cc5f44b280976
Response Header
    set-cookie
    	csrftoken=e6iYVDHUq23czYgmPeCci4EaFxulK6QvfPdGrGcUn45vm83keFOesNnbq0wu95Qx; expires=Thu, 30 Dec 2021 11:13:00 GMT; Max-Age=31449600; Path=/; SameSite=Lax; Secure
Response JSON
    csrftoken: tQrPWjhAktOmYCFNdYc4vT30ItaYM0UIuzmxsmMAhvQFLMsLCpo6FCM1tWc7bZUK

POST https://app.memrise.com/v1.17/auth/access_token/
Request Header
    X-CSRFToken
    	tQrPWjhAktOmYCFNdYc4vT30ItaYM0UIuzmxsmMAhvQFLMsLCpo6FCM1tWc7bZUK
    Cookie
    	ajs_anonymous_id=%2237e4a393-1545-4bbc-bc6d-01e0e3dfdc5a%22;
    	G_ENABLED_IDPS=google;
    	ab.storage.sessionId.81b5a720-d869-44a3-b051-fbf0e709467a=%7B%22g%22%3A%22a9b80de1-19c8-9370-7d7a-9e48ad7cc2de%22%2C%22e%22%3A1609413161834%2C%22c%22%3A1609413131813%2C%22l%22%3A1609413131834%7D;
    	ab.storage.deviceId.81b5a720-d869-44a3-b051-fbf0e709467a=%7B%22g%22%3A%2245f543bb-c766-07bb-169b-9d9a241a7399%22%2C%22c%22%3A1609413131815%2C%22l%22%3A1609413131815%7D;
    	_gcl_au=1.1.1566296011.1609413132; __stripe_mid=7954b20f-3ea1-430a-911f-0b588469e247a4a44c;
    	__stripe_sid=d7d1b258-fad7-41ed-9659-43d87cc5f44b280976;
    	csrftoken=tQrPWjhAktOmYCFNdYc4vT30ItaYM0UIuzmxsmMAhvQFLMsLCpo6FCM1tWc7bZUK
Request JSON
    client_id	"1e739f5e77704b57a703"
    grant_type	"password"
    password	"66b1d91e8e66b1d91e8e!"
    username	"66b1d91e8e"
Response JSON
    access_token	Object { access_token: "f6c2790175911170bbff77366a444ed48e28c4e3", token_type: "Bearer", expires_in: 315359999, … }
    access_token	"f6c2790175911170bbff77366a444ed48e28c4e3"
    token_type	"Bearer"
    expires_in	315359999
    scope	"read"
    user	Object { username: "66b1d91e8e", is_new: false, id: 34497740 }
    username	"66b1d91e8e"
    is_new	false
    id	34497740

GET https://app.memrise.com/v1.17/auth/web/?invalidate_token_after=true&token=f6c2790175911170bbff77366a444ed48e28c4e3
Request Header
    Cookie
    	ajs_anonymous_id=%2237e4a393-1545-4bbc-bc6d-01e0e3dfdc5a%22;
    	G_ENABLED_IDPS=google;
    	ab.storage.sessionId.81b5a720-d869-44a3-b051-fbf0e709467a=%7B%22g%22%3A%22a9b80de1-19c8-9370-7d7a-9e48ad7cc2de%22%2C%22e%22%3A1609413161834%2C%22c%22%3A1609413131813%2C%22l%22%3A1609413131834%7D;
    	ab.storage.deviceId.81b5a720-d869-44a3-b051-fbf0e709467a=%7B%22g%22%3A%2245f543bb-c766-07bb-169b-9d9a241a7399%22%2C%22c%22%3A1609413131815%2C%22l%22%3A1609413131815%7D;
    	_gcl_au=1.1.1566296011.1609413132;
    	__stripe_mid=7954b20f-3ea1-430a-911f-0b588469e247a4a44c;
    	__stripe_sid=d7d1b258-fad7-41ed-9659-43d87cc5f44b280976;
    	csrftoken=tQrPWjhAktOmYCFNdYc4vT30ItaYM0UIuzmxsmMAhvQFLMsLCpo6FCM1tWc7bZUK
Response Header
    set-cookie
    	csrftoken=cwS6r0gFdQyIcESJamdwjqrpBIAMz5mltECTvXolpvF7jiTbGpRp67tDNTFrj1kX; expires=Thu, 30 Dec 2021 11:13:01 GMT; Max-Age=31449600; Path=/; SameSite=Lax; Secure
    set-cookie
    	sessionid_2=zwrpo2uktmjzby5fla2wl23nlm0vcuto4; Domain=app.memrise.com; expires=Fri, 31 Dec 2021 17:13:01 GMT; HttpOnly; Max-Age=31557600; Path=/; SameSite=Lax; Secure

GET https://app.memrise.com/home/
Request Header
    Cookie
    	ajs_anonymous_id=%2237e4a393-1545-4bbc-bc6d-01e0e3dfdc5a%22;
    	G_ENABLED_IDPS=google;
    	ab.storage.sessionId.81b5a720-d869-44a3-b051-fbf0e709467a=%7B%22g%22%3A%2257febfd0-f914-e3c6-cb16-b93974e63e9c%22%2C%22e%22%3A1609413211367%2C%22c%22%3A1609413181368%2C%22l%22%3A1609413181368%7D;
    	ab.storage.deviceId.81b5a720-d869-44a3-b051-fbf0e709467a=%7B%22g%22%3A%2245f543bb-c766-07bb-169b-9d9a241a7399%22%2C%22c%22%3A1609413131815%2C%22l%22%3A1609413131815%7D;
    	_gcl_au=1.1.1566296011.1609413132;
    	__stripe_mid=7954b20f-3ea1-430a-911f-0b588469e247a4a44c;
    	__stripe_sid=d7d1b258-fad7-41ed-9659-43d87cc5f44b280976;
    	csrftoken=cwS6r0gFdQyIcESJamdwjqrpBIAMz5mltECTvXolpvF7jiTbGpRp67tDNTFrj1kX;
    	sessionid_2=zwrpo2uktmjzby5fla2wl23nlm0vcuto4
Response Header
    set-cookie
    	csrftoken=cwS6r0gFdQyIcESJamdwjqrpBIAMz5mltECTvXolpvF7jiTbGpRp67tDNTFrj1kX; expires=Thu, 30 Dec 2021 11:13:01 GMT; Max-Age=31449600; Path=/; SameSite=Lax; Secure
    set-cookie
    	sessionid_2=zwrpo2uktmjzby5fla2wl23nlm0vcuto4; Domain=app.memrise.com; expires=Fri, 31 Dec 2021 17:13:01 GMT; HttpOnly; Max-Age=31557600; Path=/; SameSite=Lax; Secure

GET https://app.memrise.com/ajax/courses/dashboard/?courses_filter=most_recent&offset=0&limit=4&get_review_count=false
Request Header
    Cookie
    	ajs_anonymous_id=%2237e4a393-1545-4bbc-bc6d-01e0e3dfdc5a%22;
    	G_ENABLED_IDPS=google;
    	ab.storage.sessionId.81b5a720-d869-44a3-b051-fbf0e709467a=%7B%22g%22%3A%2257febfd0-f914-e3c6-cb16-b93974e63e9c%22%2C%22e%22%3A1609413211367%2C%22c%22%3A1609413181368%2C%22l%22%3A1609413181368%7D;
    	ab.storage.deviceId.81b5a720-d869-44a3-b051-fbf0e709467a=%7B%22g%22%3A%2245f543bb-c766-07bb-169b-9d9a241a7399%22%2C%22c%22%3A1609413131815%2C%22l%22%3A1609413131815%7D;
    	_gcl_au=1.1.1566296011.1609413132;
    	__stripe_mid=7954b20f-3ea1-430a-911f-0b588469e247a4a44c;
    	__stripe_sid=d7d1b258-fad7-41ed-9659-43d87cc5f44b280976;
    	csrftoken=oBHCl1hlhi3dPunm3zs5TtgvKZrbcMBlFJrppYp1tXaCW8oOzC6YGaiJWawQWIzX;
    	sessionid_2=zwrpo2uktmjzby5fla2wl23nlm0vcuto4;
    	i18next=fr;
    	ajs_user_id=34497740

## Signin JSON

{
  "props": {
    "locale": "fr",
    "messages": {},
    "pageProps": {}
  },
  "page": "/signin",
  "query": {},
  "buildId": "FM-2sOsdIZ1dWIgofqBeO",
  "assetPrefix": "https://static.memrise.com/webclient",
  "runtimeConfig": {
    "GOOGLE_AUTH_CLIENT_ID": "450682755860-b4fvomsrqpdepnaneodjj35kk3l1paqn.apps.googleusercontent.com",
    "MEMRISE_API_HOST": "api.memrise.com",
    "MEMRISE_ENV": "production",
    "NODE_ENV": "production",
    "OAUTH_CLIENT_ID": "1e739f5e77704b57a703",
    "SENTRY_DSN": "https://bfa88d2d48f8403a9bf32a95785e44eb@errors.memrise.com/13",
    "SENTRY_ENVIRONMENT": "production",
    "STRIPE_PUBLIC_KEY": "pk_live_zzr1GOalvE7R9CAU0ICaDfZo",
    "SEGMENT_WEB_KEY": "8ojGZrW6mEMrdDA5XfsxEBtPYSL3Bgau"
  },
  "isFallback": false,
  "customServer": true,
  "appGip": true,
  "head": [
    [
      "meta",
      {
        "name": "viewport",
        "content": "width=device-width"
      }
    ],
    [
      "meta",
      {
        "charSet": "utf-8"
      }
    ],
    [
      "title",
      {
        "children": "Memrise"
      }
    ]
  ]
}