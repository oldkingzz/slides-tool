// === Google Apps Script — paste this into Extensions > Apps Script ===
// Then: Deploy > New Deployment > Web app > Execute as "Me" > Access "Anyone" > Deploy
// Copy the web app URL into config.json

function doPost(e) {
  var data = JSON.parse(e.postData.contents);
  var cmd = data.command;
  var pres = SlidesApp.getActivePresentation();
  var result = {};

  try {
    if (cmd === "list") {
      result = listSlides_(pres);
    } else if (cmd === "add") {
      result = addSlide_(pres, data.title || "", data.body || "");
    } else if (cmd === "set") {
      result = setSlide_(pres, data.index, data.title || "", data.body || "");
    } else if (cmd === "clear") {
      result = clearSlide_(pres, data.index);
    } else if (cmd === "delete") {
      result = deleteSlide_(pres, data.index);
    } else {
      result = {error: "Unknown command: " + cmd};
    }
  } catch (err) {
    result = {error: err.message};
  }

  return ContentService
    .createTextOutput(JSON.stringify(result))
    .setMimeType(ContentService.MimeType.JSON);
}

function listSlides_(pres) {
  var slides = pres.getSlides();
  var items = [];
  for (var i = 0; i < slides.length; i++) {
    var texts = [];
    var elems = slides[i].getPageElements();
    for (var j = 0; j < elems.length; j++) {
      if (elems[j].getPageElementType() === SlidesApp.PageElementType.SHAPE) {
        var t = elems[j].asShape().getText().asString().trim();
        if (t) texts.push(t);
      }
    }
    items.push({index: i, preview: texts.join(" | ").substring(0, 120)});
  }
  return {total: slides.length, slides: items};
}

function addSlide_(pres, title, body) {
  var slide = pres.appendSlide(SlidesApp.PredefinedLayout.BLANK);
  fillSlide_(slide, title, body);
  return {index: pres.getSlides().length - 1, status: "added"};
}

function setSlide_(pres, index, title, body) {
  var slides = pres.getSlides();
  if (index < 0 || index >= slides.length) {
    return {error: "Index " + index + " out of range (total " + slides.length + ")"};
  }
  clearSlideElements_(slides[index]);
  fillSlide_(slides[index], title, body);
  return {index: index, status: "updated"};
}

function clearSlide_(pres, index) {
  var slides = pres.getSlides();
  if (index < 0 || index >= slides.length) {
    return {error: "Index " + index + " out of range (total " + slides.length + ")"};
  }
  clearSlideElements_(slides[index]);
  return {index: index, status: "cleared"};
}

function deleteSlide_(pres, index) {
  var slides = pres.getSlides();
  if (index < 0 || index >= slides.length) {
    return {error: "Index " + index + " out of range (total " + slides.length + ")"};
  }
  slides[index].remove();
  return {index: index, status: "deleted"};
}

function clearSlideElements_(slide) {
  var elems = slide.getPageElements();
  for (var i = elems.length - 1; i >= 0; i--) {
    elems[i].remove();
  }
}

function fillSlide_(slide, title, body) {
  if (title) {
    var titleBox = slide.insertTextBox(title, 50, 15, 620, 45);
    titleBox.getText().getTextStyle().setFontSize(24).setBold(true);
  }
  if (body) {
    var yOffset = title ? 70 : 15;
    var bodyBox = slide.insertTextBox(body, 50, yOffset, 620, 370);
    bodyBox.getText().getTextStyle().setFontSize(11);
  }
}

// Test function — run manually to verify it works
function testList() {
  var pres = SlidesApp.getActivePresentation();
  Logger.log(JSON.stringify(listSlides_(pres)));
}
