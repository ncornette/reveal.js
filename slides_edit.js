
var slideNum = 0;
var subSlideNum = 0;
var lineNum = -1;

$( document ).ready(function() {

    var actions = $('#mdedit').children()
    actions[0].setAttribute('class', 'col-sm-4')
    actions[1].setAttribute('class', 'col-sm-8')

    var panels = $('#mdedit-body').children()
    panels[0].setAttribute('class', 'col-sm-4')
    panels[1].setAttribute('class', 'col-sm-8')

    // Replace preview panel with iframe with slides
    $("#html_result").replaceWith('<iframe id="slides-preview" src="http://localhost:' + reveal_port + '" style="width: 100%; height: 100%"/>')

    function update_slide_position(instance) {
        cursor = instance.getCursor()
        var newLineNum = cursor.line + (cursor.ch && 1)
        if (newLineNum != lineNum) {
            lineNum = newLineNum;
            newSlideNum = 0;
            for (var i=0; i<lineNum; i++) {
                if (instance.getLine(i).match('^------[^-]*$')) {
                    newSlideNum++;
                }
            }
            
            newSubSlideNum = 0;
            for (var i=lineNum-1; i>0; i--) {
                if (instance.getLine(i).match('^---[^-]*$')) {
                    newSubSlideNum++;
                } else if (instance.getLine(i).match('^------[^-]*$')) {
                    break;
                }
            }

            if (newSlideNum != slideNum || newSubSlideNum != subSlideNum) {
                slideNum = newSlideNum;
                subSlideNum = newSubSlideNum;
                var h_v = slideNum + '/'  + subSlideNum;
                // console.log("update_slide_position: " + h_v);
                var newUrl = 'http://localhost:' + reveal_port + '/#/' + h_v;
                $('#slides-preview').attr('src', newUrl);
            }
        }
    }

    // Disable html preview
    ajaxUpdatePreview = function() {
    }

    // Move to current Slide
    myCodeMirror.on("cursorActivity", function(instance) {
        update_slide_position(instance)
    });
});

