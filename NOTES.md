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