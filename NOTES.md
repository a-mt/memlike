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
// https://www.memrise.com/community/courses/french/

var list  = document.querySelectorAll('li[data-category-id]'),
    categories_slug = {};

for(var i=0; i<list.length; i++) {
    var li   = list[i],
        id   = li.getAttribute("data-category-id"),
        code = li.firstElementChild.getAttribute("href")
                 .replace(/\/$/, '').split('/').pop();

    categories_slug[code] = id;
}
copy(categories_slug);
```

Add code to categories:

``` js
var id2code = Object.keys(categories_slug).reduce(function(obj,key){
   obj[ categories_slug[key] ] = key;
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

```
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
    	I18Next=fr;
    	ajs_user_id=34497740
```

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

## Categories photo

```
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/languages/ -O languages.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/arts-literature/ -O arts-literature.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/maths-science/ -O maths-science.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/the-natural-world/ -O the-natural-world.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/history-geography/ -O history-geography.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/memory-training/ -O memory-training.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/professional-and-careers/ -O professional-and-careers.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/standardised-tests/ -O standardised-tests.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/trivia/ -O trivia.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/entertainment/ -O entertainment.html

wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/european/ -O european.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/sami-languages/ -O sami-languages.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/chinese/ -O chinese.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/indian/ -O indian.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/asian-and-pacific/ -O asian-and-pacific.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/middle-eastern/ -O middle-eastern.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/slavic/ -O slavic.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/african/ -O african.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/native-american/ -O native-american.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/constructed-languages/ -O constructed-languages.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/sign-languages/ -O sign-languages.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/other/ -O other.html

wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/german/ -O german.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/armenian/ -O armenian.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/japanese/ -O japanese.html
wget --load-cookies mycookies.txt https://community-courses.memrise.com/de/community/courses/french/classics/ -O classics.html

files=(*.html)
for file in "${files[@]}"; do
    echo ${file/.*/};

    header=$(sed -n '/<h1/,/\/h1/p' $file);
    echo $header | sed -n 's/.*src="\([^"]*\)".*/\1/p'
done

for file in "${files[@]}"; do
    sed -n '/<li data-category-id/,/<\/li>/ {s/.*href="\([^"]*\)".*/\1/p; s/.*src="\([^"]*\)".*/\1/p}' $file
done
```

```
"african": "https://static.memrise.com/uploads/category_photos/african.png"
"afrikaans": "https://static.memrise.com/uploads/language_photos/Afrikaans.png"
"akan-twi": "https://static.memrise.com/uploads/category_photos/akan-flag.png"
"albanian": "https://static.memrise.com/uploads/category_photos/albanian.png"
"american-sign-language-asl": "https://static.memrise.com/uploads/category_photos/sign-american.png"
"ancient-greek": "https://static.memrise.com/uploads/category_photos/Ancient-Greek.png"
"animals": "https://static.memrise.com/uploads/category_photos/animals.png"
"armenian": "https://static.memrise.com/uploads/category_photos/armenian.png"
"art": "https://static.memrise.com/uploads/category_photos/art.png"
"art-music-literature": "https://static.memrise.com/uploads/category_photos/art.png"
"arts-literature": "https://static.memrise.com/uploads/category_photos/icon001.png"
"asian-and-pacific": "https://static.memrise.com/uploads/category_photos/asian-and-pacific.png"
"australian": "https://static.memrise.com/uploads/category_photos/aboriginal.gif"
"azerbaijani": "https://static.memrise.com/uploads/category_photos/azerbaijini.png"
"basque": "https://static.memrise.com/uploads/language_photos/DemoFlags-38_copy.png"
"belarusian": "https://static.memrise.com/uploads/category_photos/belarus.png"
"bengali": "https://static.memrise.com/uploads/language_photos/DemoFlags-61_copy.png"
"biology": "https://static.memrise.com/uploads/category_photos/biology.png"
"board-games": "https://static.memrise.com/uploads/category_photos/board-games.png"
"bosnian": "https://static.memrise.com/uploads/language_photos/DemoFlags-71_copy.png"
"breton": "https://static.memrise.com/uploads/language_photos/Breton-flag.png"
"bulgarian": "https://static.memrise.com/uploads/language_photos/DemoFlags-66_copy.png"
"burmese": "https://static.memrise.com/uploads/language_photos/burmese.png"
"cantonese": "https://static.memrise.com/uploads/category_photos/DemoFlags-01.png"
"cantonese-jyutping": "https://static.memrise.com/uploads/category_photos/DemoFlags-01.png"
"capitals": "https://static.memrise.com/uploads/category_photos/capitals.png"
"catalan": "https://static.memrise.com/uploads/language_photos/DemoFlags-29_copy.png"
"cebuano": "https://static.memrise.com/uploads/category_photos/Vlag_Fil_Cebu.gif"
"chemistry": "https://static.memrise.com/uploads/category_photos/chemistry.png"
"cherokee": "https://static.memrise.com/uploads/language_photos/DemoFlags-69_copy.png"
"chinese": "https://static.memrise.com/uploads/category_photos/DemoFlags-01.png"
"chinese-simplified": "https://static.memrise.com/uploads/category_photos/DemoFlags-01.png"
"chinese-traditional": "https://static.memrise.com/uploads/category_photos/zh-TW.png"
"circassian": "https://static.memrise.com/uploads/category_photos/Circassian_.png"
"classics": "https://static.memrise.com/uploads/category_photos/classics.png"
"computers-engineering": "https://static.memrise.com/uploads/category_photos/computers-engineering.png"
"coptic": "https://static.memrise.com/uploads/language_photos/DemoFlags-39_copy.png"
"cornish": "https://static.memrise.com/uploads/language_photos/Flags_Cornish_copy.png"
"croatian": "https://static.memrise.com/uploads/language_photos/DemoFlags-30_copy.png"
"czech": "https://static.memrise.com/uploads/language_photos/DemoFlags-19_copy.png"
"danish": "https://static.memrise.com/uploads/language_photos/DemoFlags-25_copy.png"
"dutch": "https://static.memrise.com/uploads/language_photos/Flags_Dutch_copy.png"
"dzongkha-2": "https://static.memrise.com/uploads/category_photos/bhutan.png"
"eastern-armenian": "https://static.memrise.com/uploads/category_photos/armenian.png"
"english": "https://static.memrise.com/uploads/category_photos/en.png"
"english-us": "https://static.memrise.com/uploads/category_photos/us_flag.png"
"entertainment": "https://static.memrise.com/uploads/category_photos/icon009.png"
"esperanto": "https://static.memrise.com/uploads/language_photos/DemoFlags-34_copy.png"
"estonian": "https://static.memrise.com/uploads/language_photos/DemoFlags-32_copy.png"
"european": "https://static.memrise.com/uploads/category_photos/european.png"
"faroese": "https://static.memrise.com/uploads/language_photos/Flags_BenExtras_Faroese.png"
"film": "https://static.memrise.com/uploads/category_photos/film.png"
"finnish": "https://static.memrise.com/uploads/language_photos/DemoFlags-22_copy.png"
"flags": "https://static.memrise.com/uploads/category_photos/flags.png"
"flemish": "https://static.memrise.com/uploads/category_photos/flemish.png"
"french": "https://static.memrise.com/uploads/language_photos/DemoFlags-02_copy.png"
"french-sign-language-lsf": "https://static.memrise.com/uploads/category_photos/sign-french.png"
"galician": "https://static.memrise.com/uploads/category_photos/galician-flag.png"
"georgian": "https://static.memrise.com/uploads/category_photos/georgian.png"
"german": "https://static.memrise.com/uploads/category_photos/german.png"
"german-2": "https://static.memrise.com/uploads/language_photos/german.png"
"greek": "https://static.memrise.com/uploads/language_photos/DemoFlags-26_copy.png"
"greenlandic": "https://static.memrise.com/uploads/category_photos/greenland.png"
"hakka": "https://static.memrise.com/uploads/category_photos/hakka.png"
"hawaiian": "https://static.memrise.com/uploads/language_photos/DemoFlags-72_copy.png"
"hebrew": "https://static.memrise.com/uploads/language_photos/DemoFlags-24_copy.png"
"hindi": "https://static.memrise.com/uploads/language_photos/DemoFlags-28_copy.png"
"history-geography": "https://static.memrise.com/uploads/category_photos/icon004.png"
"hungarian": "https://static.memrise.com/uploads/language_photos/DemoFlags-21_copy.png"
"icelandic": "https://static.memrise.com/uploads/language_photos/DemoFlags-35_copy.png"
"indian": "https://static.memrise.com/uploads/category_photos/indian.png"
"indonesian": "https://static.memrise.com/uploads/language_photos/DemoFlags-64_copy.png"
"interlingua-international-auxiliar": "https://static.memrise.com/uploads/category_photos/interlingua.png"
"irish": "https://static.memrise.com/uploads/language_photos/DemoFlags-12_copy.png"
"italian": "https://static.memrise.com/uploads/language_photos/DemoFlags-06_copy.png"
"japanese": "https://static.memrise.com/uploads/category_photos/DemoFlags-09_copy.png"
"japanese-4": "https://static.memrise.com/uploads/category_photos/DemoFlags-09_copy.png"
"japanese-no-script": "https://static.memrise.com/uploads/category_photos/DemoFlags-09_copy.png"
"javanese-2": "https://static.memrise.com/uploads/category_photos/java.jpeg"
"kanji": "https://static.memrise.com/uploads/category_photos/DemoFlags-09_copy.png"
"karen-languages": "https://static.memrise.com/uploads/language_photos/DemoFlags-54_copy.png"
"kazakh": "https://static.memrise.com/uploads/language_photos/DemoFlags-62_copy.png"
"khmer": "https://static.memrise.com/uploads/category_photos/khmer.png"
"klingon": "https://static.memrise.com/uploads/language_photos/DemoFlags-40_copy.png"
"korean": "https://static.memrise.com/uploads/category_photos/korean-flag.png"
"kurdish": "https://static.memrise.com/uploads/category_photos/kurdish-flag1.png"
"kyrgyz": "https://static.memrise.com/uploads/category_photos/kyrgyz.png"
"ladin": "https://static.memrise.com/uploads/category_photos/ladin.png"
"latin": "https://static.memrise.com/uploads/language_photos/latin.png"
"latvian": "https://static.memrise.com/uploads/language_photos/Flags_BenExtras_Latvian.png"
"lithuanian": "https://static.memrise.com/uploads/language_photos/DemoFlags-37_copy.png"
"lojban": "https://static.memrise.com/uploads/category_photos/lojban.png"
"lule-sami": "https://static.memrise.com/uploads/category_photos/sami.png"
"luxembourgish": "https://static.memrise.com/uploads/language_photos/Flags_BenExtras_Luxembourgish.png"
"macedonian": "https://static.memrise.com/uploads/language_photos/Flags_BenExtras_Macedonian.png"
"malagasy": "https://static.memrise.com/uploads/category_photos/madagascar.png"
"malay": "https://static.memrise.com/uploads/language_photos/DemoFlags-60_copy.png"
"maltese": "https://static.memrise.com/uploads/category_photos/maltese-flag1.png"
"mandarin-spoken-only": "https://static.memrise.com/uploads/category_photos/DemoFlags-01.png"
"manx": "https://static.memrise.com/uploads/language_photos/Flags_BenExtras_Manx.png"
"maori": "https://static.memrise.com/uploads/language_photos/DemoFlags-55_copy.png"
"maps": "https://static.memrise.com/uploads/category_photos/maps.png"
"marathi": "https://static.memrise.com/uploads/language_photos/DemoFlags-41_copy.png"
"marshallese": "https://static.memrise.com/uploads/category_photos/marshallese.png"
"maths": "https://static.memrise.com/uploads/category_photos/maths.png"
"maths-science": "https://static.memrise.com/uploads/category_photos/icon002.png"
"memory-palaces": "https://static.memrise.com/uploads/category_photos/memory-palaces.png"
"memory-training": "https://static.memrise.com/uploads/category_photos/icon005.png"
"middle-eastern": "https://static.memrise.com/uploads/category_photos/middle-eastern.png"
"mongolian": "https://static.memrise.com/uploads/language_photos/Flags_BenExtras_Mongolian.png"
"morse-code": "https://static.memrise.com/uploads/category_photos/morse-code.png"
"music": "https://static.memrise.com/uploads/category_photos/music.png"
"native-american": "https://static.memrise.com/uploads/category_photos/native-american.png"
"navi": "https://static.memrise.com/uploads/category_photos/navi.png"
"nepali": "https://static.memrise.com/uploads/category_photos/Nepalese.png"
"ningbo-dialect": "https://static.memrise.com/uploads/category_photos/DemoFlags-01.png"
"northern-sami": "https://static.memrise.com/uploads/category_photos/sami.png"
"norwegian": "https://static.memrise.com/uploads/language_photos/DemoFlags-23_copy.png"
"number-systems": "https://static.memrise.com/uploads/category_photos/number-systems.png"
"occitan": "https://static.memrise.com/uploads/category_photos/occitan_flag.png"
"ossetic": "https://static.memrise.com/uploads/category_photos/ossetic.png"
"other-language": "https://static.memrise.com/uploads/category_photos/other-languages.png"
"persian": "https://static.memrise.com/uploads/category_photos/farsi.png"
"physics": "https://static.memrise.com/uploads/category_photos/physics.png"
"playing-card-systems": "https://static.memrise.com/uploads/category_photos/playing-card-systems.png"
"pokemon": "https://static.memrise.com/uploads/category_photos/pokemon.png"
"polish": "https://static.memrise.com/uploads/language_photos/DemoFlags-51_copy.png"
"portuguese-brazil": "https://static.memrise.com/uploads/category_photos/pt-br.png"
"portuguese-portugal-2": "https://static.memrise.com/uploads/language_photos/DemoFlags-31_copy.png"
"professional-and-careers": "https://static.memrise.com/uploads/category_photos/icon006.png"
"psychology": "https://static.memrise.com/uploads/category_photos/psychology.png"
"quechua": "https://static.memrise.com/uploads/category_photos/quechua.png"
"quenya": "https://static.memrise.com/uploads/category_photos/quenya.png"
"romanian": "https://static.memrise.com/uploads/language_photos/Romanian.png"
"russian": "https://static.memrise.com/uploads/language_photos/DemoFlags-20_copy.png"
"sami-languages": "https://static.memrise.com/uploads/category_photos/sami.png"
"sanskrit": "https://static.memrise.com/uploads/category_photos/sanskrit.png"
"scots": "https://static.memrise.com/uploads/language_photos/DemoFlags-36_copy.png"
"scottish-gaelic": "https://static.memrise.com/uploads/category_photos/scottish-gaelic.png"
"serbian": "https://static.memrise.com/uploads/language_photos/DemoFlags-43_copy.png"
"sign-languages": "https://static.memrise.com/uploads/category_photos/sign-languages.png"
"slavic": "https://static.memrise.com/uploads/category_photos/slavic.png"
"slovak": "https://static.memrise.com/uploads/language_photos/DemoFlags-11_copy.png"
"slovenian": "https://static.memrise.com/uploads/language_photos/DemoFlags-16_copy.png"
"somali": "https://static.memrise.com/uploads/category_photos/somali.png"
"southern-sami": "https://static.memrise.com/uploads/category_photos/sami.png"
"spanish-mexico": "https://static.memrise.com/uploads/category_photos/MEX.png"
"spanish-spain": "https://static.memrise.com/uploads/language_photos/DemoFlags-03_copy.png"
"standardised-tests": "https://static.memrise.com/uploads/category_photos/icon007.png"
"stars": "https://static.memrise.com/uploads/category_photos/stars.png"
"swahili": "https://static.memrise.com/uploads/language_photos/DemoFlags-45_copy.png"
"swedish": "https://static.memrise.com/uploads/language_photos/DemoFlags-18_copy.png"
"swiss-german": "https://static.memrise.com/uploads/category_photos/swiss-german.png"
"tagalog": "https://static.memrise.com/uploads/category_photos/Tagalog.png"
"taishanese": "https://static.memrise.com/uploads/category_photos/DemoFlags-01.png"
"tamang": "https://static.memrise.com/uploads/language_photos/Tamang.png"
"tamil": "https://static.memrise.com/uploads/category_photos/tamil-flag.v1.png"
"thai": "https://static.memrise.com/uploads/language_photos/DemoFlags-47_copy.png"
"the-natural-world": "https://static.memrise.com/uploads/category_photos/icon003.png"
"tibetan": "https://static.memrise.com/uploads/language_photos/Flags_BenExtras_Tibetan.png"
"trivia": "https://static.memrise.com/uploads/category_photos/icon008.png"
"turkish": "https://static.memrise.com/uploads/language_photos/DemoFlags-13_copy.png"
"ukrainian": "https://static.memrise.com/uploads/language_photos/DemoFlags-49_copy.png"
"ume-sami": "https://static.memrise.com/uploads/category_photos/sami.png"
"urdu": "https://static.memrise.com/uploads/category_photos/urdu.png"
"vietnamese": "https://static.memrise.com/uploads/category_photos/vietnamese.png"
"welsh": "https://static.memrise.com/uploads/language_photos/Flags_Welsh_copy.png"
"western-armenian": "https://static.memrise.com/uploads/category_photos/armenian.png"
"wolof": "https://static.memrise.com/uploads/category_photos/wolof.png"
"yoga": "https://static.memrise.com/uploads/category_photos/yoga.png"
"yoruba": "https://static.memrise.com/uploads/category_photos/yoruba.png"
"zulu": "https://static.memrise.com/uploads/category_photos/Zulu.png"
```

```
https://static.memrise.com/garden/img/flag-circles/small/placeholder@2x.png
https://static.memrise.com/uploads/category_photos/aboriginal.gif
https://static.memrise.com/uploads/category_photos/akan-flag.png
https://static.memrise.com/uploads/category_photos/albanian.png
https://static.memrise.com/uploads/category_photos/Ancient-Greek.png
https://static.memrise.com/uploads/category_photos/armenian.png
https://static.memrise.com/uploads/category_photos/azerbaijini.png
https://static.memrise.com/uploads/category_photos/belarus.png
https://static.memrise.com/uploads/category_photos/bhutan.png
https://static.memrise.com/uploads/category_photos/Circassian_.png
https://static.memrise.com/uploads/category_photos/DemoFlags-01.png
https://static.memrise.com/uploads/category_photos/DemoFlags-09_copy.png
https://static.memrise.com/uploads/category_photos/en.png
https://static.memrise.com/uploads/category_photos/farsi.png
https://static.memrise.com/uploads/category_photos/flemish.png
https://static.memrise.com/uploads/category_photos/galician-flag.png
https://static.memrise.com/uploads/category_photos/georgian.png
https://static.memrise.com/uploads/category_photos/greenland.png
https://static.memrise.com/uploads/category_photos/hakka.png
https://static.memrise.com/uploads/category_photos/interlingua.png
https://static.memrise.com/uploads/category_photos/java.jpeg
https://static.memrise.com/uploads/category_photos/khmer.png
https://static.memrise.com/uploads/category_photos/korean-flag.png
https://static.memrise.com/uploads/category_photos/kurdish-flag1.png
https://static.memrise.com/uploads/category_photos/kyrgyz.png
https://static.memrise.com/uploads/category_photos/ladin.png
https://static.memrise.com/uploads/category_photos/lojban.png
https://static.memrise.com/uploads/category_photos/madagascar.png
https://static.memrise.com/uploads/category_photos/maltese-flag1.png
https://static.memrise.com/uploads/category_photos/marshallese.png
https://static.memrise.com/uploads/category_photos/MEX.png
https://static.memrise.com/uploads/category_photos/morse-code.png
https://static.memrise.com/uploads/category_photos/navi.png
https://static.memrise.com/uploads/category_photos/Nepalese.png
https://static.memrise.com/uploads/category_photos/occitan_flag.png
https://static.memrise.com/uploads/category_photos/ossetic.png
https://static.memrise.com/uploads/category_photos/other-languages.png
https://static.memrise.com/uploads/category_photos/pt-br.png
https://static.memrise.com/uploads/category_photos/quechua.png
https://static.memrise.com/uploads/category_photos/quenya.png
https://static.memrise.com/uploads/category_photos/sami.png
https://static.memrise.com/uploads/category_photos/sanskrit.png
https://static.memrise.com/uploads/category_photos/scottish-gaelic.png
https://static.memrise.com/uploads/category_photos/sign-american.png
https://static.memrise.com/uploads/category_photos/sign-french.png
https://static.memrise.com/uploads/category_photos/somali.png
https://static.memrise.com/uploads/category_photos/swiss-german.png
https://static.memrise.com/uploads/category_photos/Tagalog.png
https://static.memrise.com/uploads/category_photos/tamil-flag.v1.png
https://static.memrise.com/uploads/category_photos/urdu.png
https://static.memrise.com/uploads/category_photos/us_flag.png
https://static.memrise.com/uploads/category_photos/vietnamese.png
https://static.memrise.com/uploads/category_photos/Vlag_Fil_Cebu.gif
https://static.memrise.com/uploads/category_photos/wolof.png
https://static.memrise.com/uploads/category_photos/yoruba.png
https://static.memrise.com/uploads/category_photos/zh-TW.png
https://static.memrise.com/uploads/category_photos/Zulu.png
https://static.memrise.com/uploads/language_photos/Afrikaans.png
https://static.memrise.com/uploads/language_photos/Breton-flag.png
https://static.memrise.com/uploads/language_photos/burmese.png
https://static.memrise.com/uploads/language_photos/DemoFlags-02_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-03_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-06_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-11_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-12_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-13_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-16_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-18_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-19_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-20_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-21_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-22_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-23_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-24_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-25_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-26_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-28_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-29_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-30_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-31_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-32_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-34_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-35_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-36_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-37_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-38_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-39_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-40_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-41_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-43_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-45_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-47_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-49_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-51_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-54_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-55_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-60_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-61_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-62_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-64_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-66_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-69_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-71_copy.png
https://static.memrise.com/uploads/language_photos/DemoFlags-72_copy.png
https://static.memrise.com/uploads/language_photos/Flags_BenExtras_Faroese.png
https://static.memrise.com/uploads/language_photos/Flags_BenExtras_Latvian.png
https://static.memrise.com/uploads/language_photos/Flags_BenExtras_Luxembourgish.png
https://static.memrise.com/uploads/language_photos/Flags_BenExtras_Macedonian.png
https://static.memrise.com/uploads/language_photos/Flags_BenExtras_Manx.png
https://static.memrise.com/uploads/language_photos/Flags_BenExtras_Mongolian.png
https://static.memrise.com/uploads/language_photos/Flags_BenExtras_Tibetan.png
https://static.memrise.com/uploads/language_photos/Flags_Cornish_copy.png
https://static.memrise.com/uploads/language_photos/Flags_Dutch_copy.png
https://static.memrise.com/uploads/language_photos/Flags_Welsh_copy.png
https://static.memrise.com/uploads/language_photos/german.png
https://static.memrise.com/uploads/language_photos/latin.png
https://static.memrise.com/uploads/language_photos/Romanian.png
https://static.memrise.com/uploads/language_photos/Tamang.png

for x in "${url[@]}"; do
    filename=${x##*/};
    if [ ! -f "$filename" ]; then
        echo "$filename";
        wget "$x" -O "$filename"
    fi
done
```
