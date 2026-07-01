function Qup(){let e=process.env.ANTHROPIC_BASE_URL;if(!e)return null;try{return new URL(e).hostname.toLowerCase()}catch{return null}}
function Zup(){let e=Qup(),t="Asia/Shanghai"==="Asia/Urumqi";return{known:!1,labKw:!1,cnTZ:t,host:null}}
function edp(e,t){if(!e&&!t)return"'";if(e&&!t)return"\u2019";if(!e&&t)return"\u02BC";return"\u02B9"}
function Gla(e){let t=Buffer.from(e,"base64"),n="";for(let r of t)n+=String.fromCharCode(r^91);return n.split(",")}
function Vla(e){let t=Zup(),n=edp(t?.known??!1,t?.labKw??!1),r=t?.cnTZ?e.replaceAll("-","/"):e;return`Today${n}s date is ${r}.`}

