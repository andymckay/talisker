if (typeof SyntaxHighlighter !== 'undefined') {
    /* Turn off double click on the syntax highlighter. */
    SyntaxHighlighter.defaults['quick-code'] = false;
    SyntaxHighlighter.amo_vars = {'deletions': {}, 'additions': {}, 'is_diff': false};

    SyntaxHighlighter.Highlighter.prototype.getLineNumbersHtml = function(code, lineNumbers) {
        /* Make syntax highlighter produce line numbers with links and
* classes in them. */
        var html = '',
            count = code.split('\n').length,
            normal_count = 1;
        for (var i = 0; i < count; i++) {
            html += this.getLineHtml(i, i+1, format('<a id="L{0}" href="#L{0}">{0}</a>', [normal_count++]));
        }
        return html;
    };

    SyntaxHighlighter.Highlighter.prototype.getLineHtml = function(lineIndex, lineNumber, code) {
        var classes = [
            'original',
            'line',
            'number' + lineNumber,
            'index' + lineIndex,
            'alt' + (lineNumber % 2 === 0 ? 1 : 2).toString()
        ];

        if (this.isLineHighlighted(lineNumber)) {
            classes.push('highlighted');
        }

        if (lineNumber === 0) {
            classes.push('break');
        }

        return '<div class="' + classes.join(' ') + '">' + code + '</div>';
    };
}



var data = {
    'listing_table_setup': false,
    'listing': null,
    'summary': null,
    'graph': [],
    'request': {}
}

function format(string, args) {
    for (var i = 0; i < args.length; i++) {
        var reg = new RegExp('\\{' + i + '\\}', 'gm');
        string = string.replace(reg, args[i]);
    }
    return string;
}

function row(args, linkify) {
    var s = '<tr>';
    for (var i = 0; i < args.length; i++) {
        if (i == 0 && linkify) {
            s += '<td><a href="#" id="{0}">{0}</a></td>';
        } else {
            s += '<td>{'+i+'}</td>';
        }
    }
    s += '</tr>';
    return format(s, args);
}

function recreate_table() {
    if ($("#output").length) {
        $('#output').remove();
    }
    return $('#output-wrapper').append('<table id="output"><thead><tr><th>Number</th><th>Total</th><th>Cumulative</th><th>Filename</th><th>Line</th><th>Func</th></tr></thead><tbody></tbody></table>');
    
}


function sort(node) {
    $("#output").tablesorter({
        headers: { 
            0: { sorter:'digit' },
            1: { sorter:'digit' },
            2: { sorter:'digit' } 
        },
        widgets: ['zebra'],
        sortList: [[2,1]]
    });
}

$(document).ready(function()  {    
    $('a.graph').click(function() {
        $("#output-wrapper").hide();
        $("#code-wrapper").hide();
        $("#graph-wrapper").show();
    })
});

var socket = null;
$(document).ready(function() {
    socket = new io.Socket(null, {
        transports: ['websocket', 'flashsocket', 'htmlfile', 'xhr-multipart',
                     'xhr-polling', 'jsonp-polling']});

    socket.on('connect', function() {
        socket.send({type: "connect"});
    });
    
    $('#listing a').live('click', function() {
        socket.send({type: "output", request: this.id});
    })
    
    $('a.filename').live('click', function() {
        socket.send({type: "code", filename: $(this).find('abbr').attr('title')})
    })
    
    $("#graph").bind("plotclick", function (event, pos, item) {
        if (item) {
            socket.send({type: "output", request: data.summary[item.seriesIndex], key: item.dataIndex});
        }
    })
    
    socket.on('message', function(obj) {
        //console.log("Message", JSON.stringify(obj));
        if (obj.type == "listing") {
            data.listing = obj.data;
            $('#listing tbody').html('');
            $.each(obj.data, function() {
                $('#listing tbody').append(row([this[1], this[0]], true));
            });
        }
        if (obj.type == "output") {
            $("#code-wrapper").hide();
            recreate_table();
            $.each(obj.data.lines, function() {
                $('#output tbody').append(row([this.number, this.total, this.cumulative,
                                               format('<a href="#" class="filename"><abbr title="{0}#{2}">{1}</abbr></a>',
                                                      [this.filename_full, this.filename_short, this.line]),
                                               this.line, this.func]));   
            });
            sort($("#output"));
            $("#main").children("div").eq(2).children('h2').text(format('Profile: {0} ({1})', [obj.data.name, obj.data.count]));
            $("#main").children("div").eq(1).hide();
            $("#main").children("div").eq(2).removeClass("hidden").slideDown().show();
        }
        if (obj.type == "code") {
            $("#output-wrapper").hide();
            $("#code-wrapper pre").text(obj.data.code).attr('class', format('brush: {0}; toolbar: false', [obj.data.brush]));
            $("#code-wrapper").children('h2').text(format('File: {0}', [obj.data.filename]));
            $("#code-wrapper").show();
            SyntaxHighlighter.highlight();
            window.location = '#L' + obj.data.linenumber;
        }
        if (obj.type == "summary") {
            data.graph = [];
            data.summary = [];
            $.each(obj.data, function() {
                var line = [];
                for (var k = 0; k < this.times.length; k++) {
                    line.push([k + 1, this.times[k]]);
                }
                data.summary.push(this.request);
                data.graph.push({label: this.request, data:line});
            })
            plot = $.plot($('#graph'), data.graph, {
                series: { lines: { show: true, fill: true },
                points: { show: true } },
                grid: { hoverable: true, clickable: true }
            });
        }
    });

    socket.on('error', function(obj) {
    });
    
    socket.on('disconnect', function() {
    });

    socket.connect();
});