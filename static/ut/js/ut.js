$(document).ready(function() {
    var asyncSuccessMessage = [
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
          "<\/script>"
    ].join("");
    function get_next_instance_id_str(instance_id){
       if (instance_id==0){
           return '&next=0'
       } else {
           cr = $('tr[data-id=' + instance_id + ']') //current row
           return '&next='+cr.next("tr").data('id')
       }
    };

    $('#ModalFactory').on('click','.savechanges',function(){
        var btn=$(this)
        var form=btn.closest('form')
        var mymodal=form.closest('.modal')
        var Instance_id=form.data('instance-id')
        var Class_id=form.data('class-id')
        $.ajax({
            type : 'POST',
            url : "/Classes/edit/12345/56789/".replace(/12345/,Class_id).replace(/56789/,Instance_id),
            data : form.serialize() + '&action='+btn.attr('name') + get_next_instance_id_str(Instance_id),
            dataType : 'json',
            success: function(data) {
                if (!(data['success'])) {
            // Here we replace the form, for the
                    if (data['form_html']) {
                        form.replaceWith(data['form_html']);
                    } else {
                        form.find('.form-errors').text(data['form_errors'])
                    }
                } else {
            // Here you can show the user a success message or do whatever you need
                    //$('#instanceform').find('.success-message').show();
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
                            //$(el).DataTable().ajax.reload()
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

    function get_hlink(el){
        var class_id = el.closest('table').data('class-id')
        var instance_id = el.closest('tr').data('id')
        if (el.hasClass('viewinstance')) {
            return "/Classes/view/1111/2222".replace(/1111/,class_id).replace(/2222/,instance_id)
        } else if (el.hasClass('editinstance'))  {
            return "/Classes/edit/1111/2222".replace(/1111/,class_id).replace(/2222/,instance_id)
        } else if (el.hasClass('deleteinstance')) {
            return "/Classes/delete/1111/2222".replace(/1111/,class_id).replace(/2222/,instance_id)
        } else if (el.hasClass('createinstance')) {
            elform  = $(el).closest('.instanceform').data('instance-id')
            var eldefaults = ''
            if (elform) {
                ref_attribute=$(el).data('ref-attribute')
                ref_value=$(el).data('ref-instance-id')
                eldefaults = '?ref_attribute='+ref_attribute+'&ref_value='+ref_value
            }
            return el.data('form-url')+eldefaults
        }

    }
    //for the table rows
    $('main').on('click','.viewinstance,.editinstance,.createinstance,.deleteinstance',function () {
        //elHeight$('#ModalFactory').find('.modal')
        fmodal = $('<div class="modal fade" tabindex="-1" role="dialog" aria-hidden="true"></div>')
        mdialog = $('<div class="modal-dialog modal-xl modal-dialog-centered" role="document"></div>')
        mcontext = $('<div class="modal-content"></div>')
        $('#ModalFactory').append(fmodal.append(mdialog.append(mcontext)))
        $.ajax({
            url :  get_hlink($(this)),
            data : {},
            dataType : 'json',
            success : function (data){
                fmodal.find('.modal-content').append(data.modalformcontent);
                set_datatables()
                set_flatpickr()
            }
        })
        $(fmodal).modal('show');
    });
    $('#ModalFactory').on('show.bs.modal', '.modal', function (event) {
            var zIndex = 1040 + (10 * $('.modal:visible').length);
            $(this).css('z-index', zIndex);
            setTimeout(function() {
                $('.modal-backdrop').not('.modal-stack').css('z-index', zIndex - 1).addClass('modal-stack');
            }, 0);
    });

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
                fill_new_options(parentform,key,ops);
           });
           $.each(data.lookups,function(key, value){
                parentform.find('input[attr_id='+key+']').val(value) //!!! might be a circular reference
           });
        },
      });
    });
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
    function get_table_columns(table){
        var cols=[]
        table.find('thead th').each(function(i,el){
            cols[cols.length]={'data':$(el).text()}
        })
        return cols
    };

    function set_datatables() {
        $('.classtable').each(function (i, el) {
            if ( ! $.fn.DataTable.isDataTable($(el))) {
                var class_id = $(el).data('class-id')
                var report_id = $(el).data('report-id')
                var filter_attr=$(el).data('ref-attribute')
                var filter_val = $(el).closest('form').data('instance-id')
                var buttons = []
                if (class_id) {
                     buttons= [
                         {
                            extend: 'colvis',
                            collectionLayout: 'two-column',
                            postfixButtons: [
                                'colvisRestore',
                                {
                                    text : 'Add Column',
                                    action : function (e,dt,node,config){
                                        onclick(window.location.href='/Attributes/'+class_id+'/add')
                                    }
                                },
                                {
                                    text : 'Edit Columns',
                                    "data-form-url" : '/Attributes/'+class_id,
                                }
                            ],
                            text: "Columns",
                            },
                       {
                            text: 'Create',
                            attr : {class:'createinstance dt-button',
                                    "data-form-url" : '/Classes/edit/'+class_id+'/0',
                                    "data-ref-attribute": filter_attr,
                                    "data-ref-instance-id" : filter_val,
                                   }
                        }
                    ]
                }
                var ajax_data=[]
                var columns = [] // get_table_columns($(el));
                //$(el).preventDefault();
                var filter_data={}
                if (filter_attr) {
                    filter_data= {filtername: filter_attr, filtervalue: filter_val}
                }
                $.ajaxSetup({async:false});
                $.ajax({
                           "url": $(el).data('ajax-link'),
                           "data": filter_data,
                           "success" : function (data){
                                var hrow=$(el).find('thead tr').first().empty()
                                $.each(data.data[0], function (key, value) {
                                    if (! (key in columns)) {
                                        var my_item = {'data':key};
                                        columns.push(my_item);
                                        hrow.append('<th>'+key+'</th>')
                                    }
                                });
                                if (class_id) {
                                    hrow.append('<th>Action</th>')
                                    columns.push({'data':'Actions'})
                                }
                               ajax_data=data.data;
                           },
                           "error" : function(){
                                alert ('error loading data')
                           },
                           async : false,
                });
                $.ajaxSetup({async:true});
                var table=$(el).removeAttr('width').DataTable({
                    //searchPane:true,
                    dom: 'lBfrtip',
                    //scrollX:true,
                    data: ajax_data,
                    idSrc: 'id',
                    columns: columns,
                    columnDefs: [{
                        "targets": -1,
                        "data": null,
                        "defaultContent": '<a class="viewinstance"><i class="far fa-eye"></i></a>' +
                            '&nbsp<a class="editinstance" ><i class="far fa-edit"></i></a>' +
                            '&nbsp<a class="deleteinstance" ><i class="far fa-trash-alt"></i></a>',
                        "width":30,
                        "orderable": false
                    }],
                    fixedColumns: true,
                    stateSave: true,
                    buttons: buttons,
                    colReorder: true,
                    createdRow: function (row, data,            dataIndex) {
                        $(row).attr('data-id', data.id);
                    },
                    initComplete: function () {
                        //set_filters(this.api())
                   },
                });
                var filter_columns=[];
                $.each(columns,function(i,e){
                    filter_columns.push({'column_number':i})
                })
                //yadcf.init(table,filter_columns);

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
    set_datatables();
});


