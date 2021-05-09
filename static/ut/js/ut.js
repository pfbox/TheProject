$(document).ready(function() {
    var  asyncSuccessMessage = [
          "<div ",
          "style='position:fixed;top:0;z-index:10000;width:100%;border-radius:0;' ",
          "class='alert alert-icon alert-success alert-dismissible fade show mb-0' role='alert'>",
          "Success: Instance was updated.",
          "<button type='button' class='close' data-dismiss='alert' aria-label='Close'>",
          "<span aria-hidden='true'>&times;</span>",
          "</button>",
          "</div>",
          "<script>",
          "$('.alert').fadeTo(2000, 500).slideUp(500, function () {$('.alert').slideUp(500).remove();});",
          "</script>"
    ].join("");

    function get_next_instance_id_str(instance_id){
       if (instance_id==0){
           return 0
       } else {
           cr = $('tr[data-id=' + instance_id + ']') //current row
           return cr.next("tr").data('id')
       }
    }

    $('#ModalFactory').on('click','.send-instance-email-btn',function(){
        form=$(this).closest('form')
        $.ajax({
            type : 'POST',
            url : form.data('send-instance-email-link'),
            data : form.serialize(),
            success : function (data) {
                var mymodal = form.closest('.modal')
                mymodal.modal('hide');
            },
            error : function () {
                alert ('Error sending email!')
            }
        })
    })

    $('#ModalFactory').on('click','.deleteinstance-confirmation',function(){
        var form=$(this).closest('form')
        var class_id=form.data('class-id')
        $.ajax({
            type : 'POST',
            url : form.data('delete-instance-link'),
            data : form.serialize(),
            success : function (data) {
                if (data.success) {
                    var mymodal = form.closest('.modal')
                    mymodal.modal('hide');
                    $('.classtable[data-class-id="'+class_id+'"]').each(function(i,el){
                            if ($.fn.DataTable.isDataTable($(el))) {
                                $(el).DataTable().ajax.reload()
                            }
                    })
                } else {
                    form.find('.form-errors').text(data['error'])
                }
            },
            error : function () {
                alert ('Unknow error!')
            }
        })
    })


    $('#ModalFactory').on('click','.savechanges',function(){
        var btn=$(this)
        var form=btn.closest('form')
        var mymodal=form.closest('.modal')
        var Instance_id=form.data('instance-id')
        var Class_id=form.data('class-id')
        let data = new FormData(form.get(0))
        data.append('action',btn.attr('name'))
        data.append('next',get_next_instance_id_str(Instance_id))
        for (var value of data.values()) {
           console.log(value);
        }
        $.ajax({
            type : 'POST',
            url : "/Classes/edit/12345/56789/".replace(/12345/,Class_id).replace(/56789/,Instance_id),
            data : data,// + '&action='+btn.attr('name') + get_next_instance_id_str(Instance_id),
            processData: false,
            contentType: false,
            success: function(data) {
                if (!(data['success'])) {
            // Here we replace the form, for the
                    if (data['form_html']) {
                        form.replaceWith(data['form_html']);
                    } else {
                        form.find('.form-errors').text(data['form_errors'])
                    }
                    set_flatpickr();
                } else {
            // Here you can show the user a success message or do whatever you need
                    if ('form_html' in data) {
                        form.replaceWith(data['form_html']);
                        if (data['form_errors']) {
                            form.find('.form-errors').text(data['form_errors'])
                        }
                        set_flatpickr();
                    } else {
                       mymodal.modal('hide');
                    }
                    $('#msg').append(asyncSuccessMessage)
                    $('.classtable[data-class-id="'+Class_id+'"]').each(function(i,el){
                        if ($.fn.DataTable.isDataTable($(el))) {
                            $(el).DataTable().ajax.reload()
                        }
                    })
                }
            },
            error: function () {
                form.find('.error-message').show()
            }
        })
    });

    $("#ModalFactory").on('hidden.bs.modal','.modal', function () {
        $('.flatpickr-calendar').toggle() //???
        $(this).remove()
    });
    $('#ModalFactory').on('show.bs.modal', '.modal', function (event) {
            var zIndex = 1040 + (10 * $('.modal:visible').length);
            $(this).css('z-index', zIndex);
            setTimeout(function() {
                $('.modal-backdrop').not('.modal-stack').css('z-index', zIndex - 1).addClass('modal-stack');
            }, 0);
    });


    $("main").on('click','.send-instance-email',function(){
        var input_data = {}
        var ajax_url = ''
        var Instance_id=$(this).closest('tr').data('id')
        var form = null
        if (Instance_id){
            elements={Instance_id:Instance_id}
            ajax_url= $(this).closest('.classtable').data('send-instance-email-link')
        } else {
            form = $(this).closest('form')
            elements = form.serializeArray()
            $.each(elements,function(key,el){
                svalue=$('select[name="'+el.name+'"] option:selected').html()
                if (svalue) {
                    elements[key].value=svalue
                }
            })
            ajax_url=form.data('send-instance-email-link')
        }
        fmodal = create_modal_form_wrap()
        $('#ModalFactory').append(fmodal)
        $.ajax({
            url : ajax_url ,
            data : elements,
            success : function (data) {
                fmodal.find('.modal-content').append(data.modalformcontent);
            },
            error : function(){
                alert ('error')
            }
        })
        $(fmodal).modal('show');
    })

    $("#ModalFactory").on('show.bs.collapse','.btn-link,.dt-table',function () {
          var collapse=$(this)
          collapse.find('.classtable').each(function(i,el){
                        if ($(el).hasClass('dataTable')){
                            return
                        }
                        if (!$.fn.DataTable.isDataTable($(el))) {
                            set_datatables(collapse)
                        }
                    })
    })

    $("#ModalFactory").on('change','.hierarchy_trigger,.lookup_trigger',function () {
      var attr_id = $(this).attr('attr_id')
      var master_value  = $(this).val()
      var parentform=$(this).closest('form')
      $.ajax({
        url: "/ajax/change_master/12345".replace(/12345/, attr_id.toString()),
        data : {'value': master_value,'Attribute_id':attr_id},
        dataType: 'json',
        success: function (data) {
           $.each(data.attrs,function(key, ops){
                //fill_new_options(parentform,key,ops);
           });
           $.each(data.lookups,function(key, value){
                parentform.find('input[attr_id='+key+']').val(value) //!!! might be a circular reference
           });
        },
      });
    });

    function get_hlink(el){
        if (el.hasClass('action-item')){
            var class_id = el.data('class-id')
            var instance_id = 0
        } else {
            var class_id = el.closest('table').data('class-id')
            var instance_id = el.closest('tr').data('id')
        }
        if (el.hasClass('viewinstance')) {
            return "/Classes/view/1111/2222".replace(/1111/,class_id).replace(/2222/,instance_id)
        } else if (el.hasClass('call-viewinstance'))  {
            return "/Classes/view/1111/2222".replace(/1111/,encodeURIComponent(el.data('attribute'))).replace(/2222/,el.data('ref-instance-id'))
        } else if (el.hasClass('editinstance'))  {
            return "/Classes/edit/1111/2222".replace(/1111/,class_id).replace(/2222/,instance_id)
        } else if (el.hasClass('deleteinstance')) {
            return "/Classes/delete/1111/2222".replace(/1111/,class_id).replace(/2222/,instance_id)
        } else if (el.hasClass('createinstance')) {
            elform  = $(el).closest('.instanceform').data('instance-id')
            var eldefaults = ''
            if (elform) {
                ref_attribute=encodeURIComponent($(el).data('ref-attribute'))
                ref_value=$(el).data('ref-instance-id')
                eldefaults = '?ref_attribute='+ref_attribute+'&ref_value='+ref_value
            }
            return el.data('form-url')+eldefaults
        }
    }
    //for the table rows
    $('main').on('change','.filterfield',function(){
        var attribute_id=$(this).data('attribute-id')
        var form = $(this).closest('form')
        var class_id=form.data('class-id')
        var table = form.closest('.classtable-with-filter').find('#instances'+class_id)
        if ( $.fn.DataTable.isDataTable($(table))) {
            table.DataTable().ajax.reload()
        }
    })

    function create_modal_form_wrap(){
        fmodal = $('<div class="modal fade" role="dialog" aria-hidden="true"></div>')
        mdialog = $('<div class="modal-dialog modal-xl modal-dialog-centered" role="document"></div>')
        mcontext = $('<div class="modal-content"></div>')
        return fmodal.append(mdialog.append(mcontext))
    }

    $('main').on('click','.viewinstance,.editinstance,.createinstance,.deleteinstance,.call-viewinstance',function () {
        fmodal = create_modal_form_wrap()
        $('#ModalFactory').append(fmodal)
        var inputData={}
        if ($(this).hasClass('action-item')) {
            var form=$(this).closest('form')
            var instance_id=form.data('instance-id')
            if (instance_id==0){
                alert ('You cannot action on new instance. Please save changes.')
                return
            }
            inputData=form.serializeArray()
            inputData.push({name:'action-attribute-id',value:$(this).data('action-attribute-id')})
            inputData.push({name:'id',value:instance_id})
        }
        $.ajax({
            url :  get_hlink($(this)),
            data : inputData,
            dataType : 'json',
            success : function (data){
                fmodal.find('.modal-content').append(data.modalformcontent);
//                fmodal.find('.django-select2').djangoSelect2()
//                set_datatables(fmodal)
                set_flatpickr()
                //fmodal.find('.select2').djangoSelect2()
            }
        })
        $(fmodal).modal('show');
    });

    $('main').on('click','.deleteinstancemodal',function(){

    })

//    $(".LoadInstances").modalForm({
//        formURL: "{% url 'ut:loadinstances' Class_id %}"
//    });

    function empty_child(parentform,attr_id){
        var el = $(parentform).find('select[masterattr_id='+attr_id+']')
            if (el.length) {
               var attr_id = el.attr('attr_id')
               el.empty()
               el.append($("<option></option>").attr("value",0).text('(None)'));
               empty_child(attr_id)
            }
    }
    function fill_new_options(parentform,attr_id,options) {
         var  sel=parentform.find('select[attr_id='+attr_id+']')
         sel.empty()
         sel.append($("<option></option>").attr("value",0).text('(None)'));
         $.each(options,function(i,name){
             sel.append($("<option></option>")
                .attr("value", i)
                .text(name));
         });
         empty_child(parentform,attr_id);
    }

    function set_flatpickr() {
        flatpickr(".datetimeinput", {
            enableTime: true,
            enableSeconds: false,
            dateFormat: "Y-m-d H:i",
            allowInput: true,
    //           appendTo : window.document.querySelector('#putflatpickrhere'),
            position : "auto auto",
        });
        flatpickr(".dateinput", {
            enableTime: false,
            allowInput: true,
            enableSeconds: false,
            dateFormat: "Y-m-d",
    //           appendTo :window.document.querySelector('#putflatpickrhere'),
        });
        flatpickr(".timeinput", {
            enableTime: true,
            noCalendar: true,
            allowInput: true,
            time_24hr: true,
            enableSeconds: false,
            dateFormat: "H:i",
    //           appendTo : window.document.querySelector('#putflatpickrhere'),
        });
    };
    $('#ModalFactory').on('shown.bs.modal','.modal',function(){
        //set_flatpickr();
    })

    function set_datatables(mel) {
        $(mel).find('.classtable').each(function (i, el) {
            if ( ! $.fn.DataTable.isDataTable($(el))) {
                var filter_attr = $(el).data('ref-attribute')
                var filter_val = $(el).closest('form').data('instance-id')
                var class_id = $(el).data('class-id')
                var report_id = $(el).data('report-id')
                var buttons = []
                var columnDefs = []
                var fixedColumns = {}
                var colReorder = {}
                var dom = 't'
                if (class_id) {
                    fixedColumns = {leftColumns: 0,rightColumns: 1}
                    colReorder = { fixedColumnsRight : 1 }
                    dom = 'lBfrtip'
                    buttons = [
                        {
                            extend: 'colvis',
                            collectionLayout: 'two-column',
                            postfixButtons: [
                                'colvisRestore',
                                {
                                    text: 'Add Column',
                                    action: function (e, dt, node, config) {
                                        onclick(window.location.href = '/Attributes/' + class_id + '/add')
                                    }
                                },
                                {
                                    text: 'Edit Columns',
                                    "data-form-url": '/Attributes/' + class_id,
                                }
                            ],
                            text: "Columns",
                        },

                        {
                            text: 'Create',
                            attr: {
                                class: 'createinstance dt-button',
                                "data-form-url": '/Classes/edit/' + class_id + '/0',
                                "data-ref-attribute": filter_attr,
                                "data-ref-instance-id": filter_val,
                            }
                        },
                        {
                            text: 'Action',
                            extend: 'collection',
                            buttons: [
                                'copy', 'csv',
                                {
                                    extend: 'excelHtml5',
                                    title: '',
                                    filename: 'uttable' + class_id
                                },
                                'pdf', 'print',
                                {
                                    text: 'Load',
                                    action: function (e, dt, node, config) {
                                        //This will send the page to the location specified
                                        window.location.href = '/Load/' + class_id;
                                    }
                                },
                            ]

                        },
                        {
                            text: 'Filter',
                            attr: {
                                class: "dt-button",
                                className: "btn btn-link",
                                'type': "button",
                                'data-toggle': "collapse",
                                'data-target': "#collapseOne",
                                'aria-expanded': "false",
                                'aria-controls': "collapseOne",
                            }

                        }
                    ]
                    columnDefs = [{
                        "targets": -1,
                        "data": null,
                        "defaultContent": '<a class="viewinstance"><i class="far fa-eye"></i></a>'
                            + '&nbsp<a class="editinstance" ><i class="far fa-edit"></i></a>'
                            + '&nbsp<a class="deleteinstance" ><i class="far fa-trash-alt"></i></a>'
                            + '&nbsp<a class="send-instance-email" ><i class="far fa-envelope-open"></i></a>'
                        ,
                        "width": 64,
                        "orderable": false
                        },
                    ]
                }
                //$(el).preventDefault();
                $.ajaxSetup({async: false});
                if (true) { // if
                    var ajax_response = get_table_columns(el)
                }
                //var ajax_data=ajax_response.ajax_data
                var ajax_columns=ajax_response.ajax_columns
                $.ajaxSetup({async:true});
                var table=$(el).removeAttr('width').DataTable({
                    //searchPane:true,
                    dom: dom,
                    scrollX:true,
                    serverSide: true,
                    ajax : {
                        url : $(el).data('ajax-link'),
                        data : function (d){
                                return $.extend(d,create_filter_data(el))
                        }
                    },
                    //data: ajax_data,
                    idSrc: 'id',
                    columns: ajax_columns,
                    columnDefs: columnDefs,
                    fixedColumns: fixedColumns,
                    stateSave: true,
                    buttons: buttons,
                    colReorder: colReorder,
                    createdRow: function (row, data,            dataIndex) {
                        $(row).attr('data-id', data.id);
                    },
                    initComplete: function () {
                        //set_filters(this.api())
                   },
                });
                //only search on "Enter" key
                $(el).closest('.dataTables_wrapper').find(".dataTables_filter input")
                    .unbind()
                    .bind('keyup change', function (e) {
                    if (e.keyCode == 13 || this.value == "") {
                        table.search(this.value).ajax.reload()
                    }
                });
            }
        });
    };
    function set_filters(api){
                      //var api = this.api();
        $('.filterhead', api.table().header()).each( function (i) {
            var column = api.column(i);
            //var label = $("<label>"+$(column.header()).html()+"</label>")
            var select = $('<select><option value=""></option></select>')
                .appendTo( $(this) )
                .on( 'change', function () {
                    var val = $.fn.dataTable.util.escapeRegex(
                        $(this).val()
                    );
                    column
                        .search( val ? '^'+val+'$' : '', true, false )
                        .draw();
                } );
            column.data().unique().sort().each( function ( d, j ) {
                select.append( '<option value="'+d+'">'+d+'</option>' );
            } );
        } );
    };

    function create_filter_data(el) {
        var filterform = $(el).closest('.classtable-with-filter').find('.classtablefilter')
        var filter_val = $(el).closest('form').data('instance-id')
        var filter_attr = $(el).data('ref-attribute')
        var class_id = $(el).data('class-id')
        var report_id = $(el).data('report-id')
        var filter_data = {filterform: JSON.stringify(filterform.serializeArray())}
        if (filter_attr) {
            filter_data['filtername'] = filter_attr
            filter_data['filtervalue'] = filter_val
        }
        return filter_data
    }

    function get_table_columns(el){
        var ajax_columns=[]
        var class_id = $(el).data('class-id')
        var report_id = $(el).data('report-id')
        $.ajax({
            "url": $(el).data('ajax-columns-link'),
            "success" : function (data){
                    var hrow = $(el).find('thead tr').first().empty()
                    $.each(data.columns, function (key,dt) {
                        var my_item = {'data': key};
                        if (dt=='hlink'){
                            my_item['render'] = function ( data, type, row, meta ) {
                                if (data) {
                                    return '<a href="//' + data + '">'+'click...'+'</a>';
                                }  else {
                                    return data
                                }
                            }
                        } else if (dt=='instance') {
                            my_item['render'] = function ( data, type, row, meta ) {
                                if (data) {
                                    return '<a class="call-viewinstance" href="javascript:void(0)" data-attribute="'+key+'" data-ref-instance-id="'+row.id+'">'+data+'</a>';
                                }  else {
                                    return data
                                }
                            }
                        } else if (dt=='file') {
                            my_item['render'] = function ( data, type, row, meta ) {
                                if (data) {
                                    ds=data.split(';')
                                    return '<a class="file-to-download" href="/download_file/'+ds[0]+'" data-file-id="'+ds[0]+'" data-ref-instance-id="'+row.id+'">'+ds[1]+'</a>';
                                }  else {
                                    return data
                                }
                            }
                        }
                        ajax_columns.push(my_item);
                        hrow.append('<th>' + key + '</th>')
                    });
                    if (class_id) {
                        hrow.append('<th>Action</th>')
                        ajax_columns.push({'data': 'Actions'})
                    }
                },
            "error" : function(){
                alert ('error loading data')
            },
            async : false,
        });
        return {'ajax_columns':ajax_columns}
    }
    set_datatables('main');
//    create_filter_data('.classtable')
});


