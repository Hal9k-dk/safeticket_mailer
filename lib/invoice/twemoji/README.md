# Intro

All the files in the folder comes from a git repo

__Source:__ https://github.com/makepanic/twemoji-clean/tree/master/2

__Commit:__ 06d0516b06447be0fca1dbeaf0fe36fac8693083

I copied it to have all the files local in order not to be dependent on the 3rd resources


# Patch
I modified the files `twemoji.js` and changed line 27 from
```js
      base: 'https://twemoji.maxcdn.com/v/13.0.2/',
```
to
```js
      base: '%%%TWEMOJI_JS_CONTENT%%%/',
```
to use local resources instead of the CDN
