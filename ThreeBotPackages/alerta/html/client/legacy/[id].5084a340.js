import{_ as n,a as t,b as r,c as i,i as c,s as o,d as u,S as e,A as a,o as f,x as s,G as m,w as l,k as d,O as p,F as A,r as $,n as y,y as v,t as g,j as h,z as w}from"./index.4ecb9288.js";import{_ as x,a as b}from"./index.d89e26f3.js";import{c as j,S as k,A as S}from"./Spinner.d1c1365c.js";function N(n){var t,r=new k({});return{c:function(){r.$$.fragment.c()},l:function(n){r.$$.fragment.l(n)},m:function(n,i){$(r,n,i),t=!0},p:y,i:function(n){t||(l(r.$$.fragment,n),t=!0)},o:function(n){s(r.$$.fragment,n),t=!1},d:function(n){v(r,n)}}}function _(n){var t,r,i,c,o=[F,z],u=[];function e(n,t){return t.myAlert.id?0:1}return t=e(0,n),r=u[t]=o[t](n),{c:function(){r.c(),i=a()},l:function(n){r.l(n),i=a()},m:function(n,r){u[t].m(n,r),f(n,i,r),c=!0},p:function(n,c){var a=t;(t=e(0,c))===a?u[t].p(n,c):(A(),s(u[a],1,1,function(){u[a]=null}),m(),(r=u[t])||(r=u[t]=o[t](c)).c(),l(r,1),r.m(i.parentNode,i))},i:function(n){c||(l(r),c=!0)},o:function(n){s(r),c=!1},d:function(n){u[t].d(n),n&&d(i)}}}function z(n){var t,r,i;return{c:function(){t=g("Alert of "),r=g(n.id),i=g(" cannot be found")},l:function(c){t=h(c,"Alert of "),r=h(c,n.id),i=h(c," cannot be found")},m:function(n,c){f(n,t,c),f(n,r,c),f(n,i,c)},p:function(n,t){n.id&&w(r,t.id)},i:y,o:y,d:function(n){n&&(d(t),d(r),d(i))}}}function F(n){var t,r=new S({props:{myAlert:n.myAlert}});return{c:function(){r.$$.fragment.c()},l:function(n){r.$$.fragment.l(n)},m:function(n,i){$(r,n,i),t=!0},p:function(n,t){var i={};n.myAlert&&(i.myAlert=t.myAlert),r.$set(i)},i:function(n){t||(l(r.$$.fragment,n),t=!0)},o:function(n){s(r.$$.fragment,n),t=!1},d:function(n){v(r,n)}}}function G(n){var t,r,i,c,o=[_,N],u=[];function e(n,t){return t.myAlert?0:1}return t=e(0,n),r=u[t]=o[t](n),{c:function(){r.c(),i=a()},l:function(n){r.l(n),i=a()},m:function(n,r){u[t].m(n,r),f(n,i,r),c=!0},p:function(n,c){var a=t;(t=e(0,c))===a?u[t].p(n,c):(A(),s(u[a],1,1,function(){u[a]=null}),m(),(r=u[t])||(r=u[t]=o[t](c)).c(),l(r,1),r.m(i.parentNode,i))},i:function(n){c||(l(r),c=!0)},o:function(n){s(r),c=!1},d:function(n){u[t].d(n),n&&d(i)}}}function O(n,t){return q.apply(this,arguments)}function q(){return(q=x(b.mark(function n(t,r){var i;return b.wrap(function(n){for(;;)switch(n.prev=n.next){case 0:return i=t.params.id,n.abrupt("return",{id:i});case 2:case"end":return n.stop()}},n)}))).apply(this,arguments)}function B(n,t,r){var i=t.id,c=t.myAlert;return p(x(b.mark(function n(){return b.wrap(function(n){for(;;)switch(n.prev=n.next){case 0:j(i).then(function(n){r("myAlert",c=n.data)});case 1:case"end":return n.stop()}},n)}))),n.$set=function(n){"id"in n&&r("id",i=n.id),"myAlert"in n&&r("myAlert",c=n.myAlert)},{id:i,myAlert:c}}export default(function(a){function f(n){var e;return t(this,f),e=r(this,i(f).call(this)),c(u(e),n,B,G,o,["id","myAlert"]),e}return n(f,e),f}());export{O as preload};