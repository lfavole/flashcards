function cleanNumber(number) {
    return +number.replace(/,/g, ".").replace(/ /g, "");
}
function suffix2num(suffix) {
    var power = " kmgtpezy".indexOf(suffix[0].toLowerCase());
    if(power == -1) return 1024;
    return 1024 ** power;
}
function filesize2num(filesize) {
    var matches = filesize.match(/^([\d ]+([.,][\d ]+)?) ?([KMGTPEZY]i?[Bo]?|[Bo])$/i);
    if(!matches) return -1;
    return cleanNumber(matches[1]) * suffix2num(matches[3]);
}
function date2num(filesize) {
    var matches = filesize.match(/^(\d\d)\/(\d\d)\/(\d\d\d\d) (\d\d):(\d\d):(\d\d)/i);
    if(!matches) return;
    return +("" + matches[3] + matches[2] + matches[1] + matches[4] + matches[5] + matches[6]);
}

Tablesort.extend(
    "number",
    item => !isNaN(cleanNumber(item)),
    (a, b) => cleanNumber(b) - cleanNumber(a),
);
Tablesort.extend(
    "filesize",
    item => filesize2num(item) != -1,
    (a, b) => filesize2num(b) - filesize2num(a),
);
Tablesort.extend(
    "date",
    item => date2num(item),
    (a, b) => date2num(b) - date2num(a),
);

document$.subscribe(function() {
    document.querySelectorAll("article table:not([class])").forEach(table => new Tablesort(table));
});
