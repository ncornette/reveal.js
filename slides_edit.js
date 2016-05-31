
var slideNum = 0;
var subSlideNum = 0;
var lineNum = 0;

$( document ).ready(function() {

    var panels = $('#mdedit-body').children()
    panels[0].setAttribute('class', 'col-sm-4')
    panels[1].setAttribute('class', 'col-sm-8')

    // Replace preview panel with iframe with slides
    $("#html_result").replaceWith('<iframe id="slides-preview" src="http://localhost:8424" style="width: 100%; height: 100%"/>')

    // Disable html preview
    ajaxUpdatePreview = function() {}

    // Move to current Slide
    myCodeMirror.on("cursorActivity", function(instance) {
        var newLineNum = instance.getCursor().line
        if (newLineNum != lineNum) {
            lineNum = newLineNum;
            newSlideNum = 0;
            for (var i=0; i<lineNum; i++) {
                if (instance.getLine(i) == '------') {
                    newSlideNum++;
                }
            }
            
            newSubSlideNum = 0;
            for (var i=lineNum-1; i>0; i--) {
                if (instance.getLine(i) == '---') {
                    newSubSlideNum++;
                } else if (instance.getLine(i) == '------') {
                    break;
                }
            }

            if (newSlideNum != slideNum || newSubSlideNum != subSlideNum) {
                slideNum = newSlideNum;
                subSlideNum = newSubSlideNum;
                var newUrl = 'http://localhost:8424/#/' + slideNum + '/'  + subSlideNum
                $('#slides-preview').attr('src', newUrl)
            }
        }
    });
});

