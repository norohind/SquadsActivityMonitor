window.addEventListener("load", () => {
    let xhr = new XMLHttpRequest();
    let api_endpoint = location.protocol + '//' + location.host + '/api' + location.pathname + location.search;
    if (location.search.substring(0, 1) == '?') { // params already exists
        api_endpoint = api_endpoint + '&pretty_keys=true';

    } else {
        api_endpoint = api_endpoint + '?pretty_keys=true';
    }

    table = document.getElementById('table0div');
    xhr.open('GET', api_endpoint)

    xhr.onload = function() {
        table = document.getElementById('table0div');
        if (xhr.status != 200) {
            table.innerHTML = 'Error: ' + xhr.status + '; ' + xhr.response;
        } else {
            table.innerHTML = '';
        }

        table_in_json = JSON.parse(xhr.response);

        table.appendChild(buildHtmlTable(table_in_json)); // build table

        var table = document.querySelector("#table0div > table")
        var header = table.rows[0]

        for (var i = 0, cell; cell = header.cells[i]; i++) {
            if (cell.innerText.includes('{{ target_column_name }}')) {
                var target_column_id = i;
                break;
            }
        }

        if (target_column_id == null) { // don't to anything if no action_id in the table
            return;
        }

        for (var i = 1, row; row = table.rows[i]; i++) { // append to target column filed href
            row.cells[target_column_id].innerHTML = '<td><a href="' + '{{ target_new_url }}' + table.rows[i].cells[target_column_id].innerText + ' ">' + table.rows[i].cells[target_column_id].innerText + '</a></td>';
        }
    }

    xhr.onerror = function() { // происходит, только когда запрос совсем не получилось выполнить
        table.innerHTML = 'Loading Error';
    };

    xhr.send()
    table.innerHTML = 'Loading: waiting for server response';
})