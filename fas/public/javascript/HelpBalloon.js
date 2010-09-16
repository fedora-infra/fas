// 
// Copyright (c) 2008 Beau D. Scott | http://www.beauscott.com
// 
// Permission is hereby granted, free of charge, to any person
// obtaining a copy of this software and associated documentation
// files (the "Software"), to deal in the Software without
// restriction, including without limitation the rights to use,
// copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the
// Software is furnished to do so, subject to the following
// conditions:
// 
// The above copyright notice and this permission notice shall be
// included in all copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
// EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
// OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
// NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
// HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
// WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
// FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
// OTHER DEALINGS IN THE SOFTWARE.
// 

/**
 * HelpBalloon.js
 * Prototype/Scriptaculous based help balloons / dialog balloons
 * @version 1.5
 * @requires prototype.js <http://www.prototypejs.org/>
 * @requires scriptaculous.js <http://script.aculo.us/>
 * @author Beau D. Scott <beau_scott@hotmail.com>
 */
var HelpBalloon = Class.create();
HelpBalloon.prototype = {
	/**
	 * Instantiates the object
	 * @param {Object} options
	 * @see HelpBalloonOptions
	 * @constructor
	 */
	initialize: function(options)
	{
		/**
		 * Display and behavioral options
		 * @see HelpBalloonOptions
		 */
		this.options = new HelpBalloonOptions();
		Object.extend(this.options, options || {});
		
		/**
		 * The local store of 'title'. Will change if the balloon is making a remote call
		 * unless options.title is specified
		 * @var {String}
		 * @private
		 */
		 this.title = this.options.title;
		
		/**
		 * Display elements
		 * @var {Object}
		 * @private
		 */
		this._elements = new HelpBalloonElements();

		/**
		 * The balloons visibility state.
		 * @var {Boolean}
		 * @private
		 */
		this.visible = false;
		
		/**
		 * Rendering status
		 * @var {Boolean}
		 * @private
		 */
		this.drawn = false;			
		
		/**
		 * X/Y coordinate of icon at time of render
		 * @var {Array}
		 * @private
		 */							
		this.renderXY = [0,0];				
		
		/**
		 * Stores the balloon coordinates
		 * @private
		 * @var {Object}
		 */					
		this.balloonCoords = null;
					
		/**
		 * Balloon styling
		 * @private
		 * @var {Object}
		 */					
		this.balloonStyle = {									
			'position': 'absolute',
			'border': 'none',
			'display': 'none'
		}
		
		/**
		 * Title Bar style
		 * @var {Object}
		 * @private
		 */
		this.titleStyle = {
			'color': 'black',
			'fontSize': '16px',
			'fontWeight': 'bold',
			'fontFamily': 'Verdana'
		}
		
		/**
		 * Width,height of the balloons
		 * @private
		 * @var {Array}
		 */
		this.balloonDimensions = [0,0];
		
		/**
		 * ID for object and Icon, Requires prototype.improvements.js
		 * @var {String}
		 */
		this.id = "HelpBalloon_" + Object.genGUID();
		
		//
		// Preload the balloon and button images so they're ready
		// at render time
		//
		// 0 1
		//  X
		// 2 3
		//
		for(var i = 0; i < 4; i++)
		{
			var balloon = new Element('img', {
				src: this.options.balloonPrefix + i + this.options.balloonSuffix
			});
			this._elements.balloons.push(balloon.src);
		}
		/**
		 * @private
		 */
		this.lastBalloon = balloon;
		
		this._elements.button = new Element('img', {
			src: this.options.button
		});
		
		//
		// Create the anchoring icon, or attach the balloon to the given icon element
		// If a string is passed in, assume it's a URL, if it's an object, assume it's
		// a DOM member.
		//
		if(typeof this.options.icon == 'string')
		{
			this._elements.icon = new Element('img', {
				src: this.options.icon,
				id: this.id + "_icon"
			});
			this._elements.icon.setStyle('cursor', 'pointer');
		}
		else
		{
			// Not a string given (most likely an object. Do not append the element
			// Kind of a hack for now, but I'll fix it in the next version.
			
			this._elements.icon = this.options.icon;
			this.options.returnElement = true; 
		}
		
		this._elements.icon._HelpBalloon = this;
			
		//
		// Attach rendering events
		//

		for(i = 0; i < this.options.useEvent.length; i++)
		{
			Event.observe(this._elements.icon, this.options.useEvent[i], this.toggle.bindAsEventListener(this));
		}
		
		this._elements.container = new Element('div', {
			'_HelpBalloon': this
		});

		//
		// If we are not relying on other javascript to attach the anchoring icon
		// to the DOM, we'll just do where the script is called from. Default behavior.
		//
		// If you want to use external JavaScript to attach it to the DOM, attach this._elements.icon
		//
		if(!this.options.returnElement)
		{
			document.write('<span id="' + this.id + '"></span>');
			var te = $(this.id);
			var p = te.parentNode;
			p.insertBefore(this._elements.icon, te);
			p.removeChild(te);
		}
	},
	
	/**
	 * Toggles the help balloon
	 * @param {Object} e Event
	 */
	toggle: function(e)
	{
		if(!e) e = window.event || {type: this.options.useEvent, target: this._elements.icon};
		var icon = Event.element(e);

		if(e.type == this.options.useEvent && !this.visible && icon == this._elements.icon)
			this.show();
		else
			this.hide();
	},

	/**
	 * Triggers the balloon to appear
	 */
	show: function()
	{
		if(!this.drawn) this._draw();
		this._reposition();
		this._hideOtherHelps();

		Effect.Appear(this._elements.container, {
			duration: this.options.duration,
			afterFinish: function(e){
				this._elements.container.setStyle('display', 'block');
				this._hideLowerElements();
			}.bindAsEventListener(this)
		});
		this.visible = true;
		Event.observe(window, 'resize', this._reposition.bindAsEventListener(this));
	},

	/**
	 * Hides the balloon
	 */
	hide: function()
	{
		this._showLowerElements();
		Effect.Fade(this._elements.container, {duration: this.options.duration});
		
		setTimeout(function(){
				this._elements.container.setStyle('display', 'none');
			}.bind(this), this.options.duration * 1000);
			
		this.visible = false;
		Event.stopObserving(window, 'resize', this._reposition.bindAsEventListener(this));
	},
	
	/**
	 * Redraws the balloon based on the current coordinates of the icon.
	 * @private
	 */
	_reposition: function()
	{
		this.balloonCoords = this._getXY(this._elements.icon);
		//Horizontal and vertical offsets in relation to the icon's 0,0 position.
		// Default is the middle of the object
		var ho = this._elements.icon.offsetWidth / 2;
		var vo = this._elements.icon.offsetHeight / 2;
		
		var offsets = this.options.anchorPosition.split(/\s+/gi);
		for(var i = 0; i < offsets.length; i++)
		{
			switch(offsets[i].toLowerCase())
			{
				case 'left':
						ho = 0;
					break;
				case 'right':
						ho = this._elements.icon.offsetWidth;
					break;
				case 'center':
						ho = this._elements.icon.offsetWidth / 2;
					break;
				case 'top':
						vo = 0;
					break;
				case 'middle':
						vo = this._elements.icon.offsetHeight / 2;
					break;
				case 'bottom':
						vo = this._elements.icon.offsetHeight;
					break;	
			}
		}
		
		this.balloonCoords.y += vo;
		this.balloonCoords.x += ho;
		
		//
		// Figure out what position to show based on available realestate
		// 0 1
		//  X
		// 2 3
		// Number indicates position of corner opposite anchor
		//
		var pos = 1;
		var offsetHeight = this.balloonCoords.y - this.balloonDimensions[1];
		if(offsetHeight < 0)
			pos += 2;

		var offsetWidth = this.balloonCoords.x + this.balloonDimensions[0];
		var ww = Browser.isMSIE() ? document.body.clientWidth : window.outerWidth;
		if(offsetWidth > ww)
			pos -- ;

		var zx = 0;
		var zy = 0;
		
		//
		// 0 1
		//  X
		// 2 3
		//
		switch(pos)
		{
			case 0:
				zx = this.balloonCoords.x - this.balloonDimensions[0];
				zy = this.balloonCoords.y - this.balloonDimensions[1];
				break;
			
			case 1:
				zx = this.balloonCoords.x;
				zy = this.balloonCoords.y - this.balloonDimensions[1];
				break;
			
			case 2:
				zx = this.balloonCoords.x - this.balloonDimensions[0];
				zy = this.balloonCoords.y;
				break;
			
			case 3:
				zx = this.balloonCoords.x;
				zy = this.balloonCoords.y;
				break;
		}
		var containerStyle = {
			/*'backgroundRepeat': 'no-repeat',
			'backgroundColor': 'transparent',
			'backgroundPosition': 'top left',*/
			'left' 	: zx + "px",
			'top'	: zy + "px",
			'width' : this.balloonDimensions[0] + 'px',
			'height' : this.balloonDimensions[1] + 'px'
		}
		if(Browser.isMSIE())
		{
			//
			// Fix for IE alpha transparencies
			//
			if(this._elements.balloons[pos].toLowerCase().indexOf('.png') > -1)
			{
				Element.setStyle(this._elements.bgContainer, {
					'left' 		: '0px',
					'top'		: '0px',	
					'filter'	: "progid:DXImageTransform.Microsoft.AlphaImageLoader(src='" + this._elements.balloons[pos] + "', sizingMethod='scale')",
					'width' 	: this.balloonDimensions[0] + 'px',
					'height' 	: this.balloonDimensions[1] + 'px',
					'position'	: 'absolute'
				});
			}
			else
				containerStyle['background'] = 'transparent url(' + this._elements.balloons[pos] + ') top left no-repeat';
		}
		else
		{
				containerStyle['background'] = 'transparent url(' + this._elements.balloons[pos] + ') top left no-repeat';
		}
		Element.setStyle(this._elements.container, containerStyle);
	},

	/**
	 * Render's the Balloon
	 * @private
	 */
	_draw: function()
	{
		Element.setStyle(this._elements.container, this.balloonStyle);
		if(this.options.dataURL && (!this.drawn || !this.options.cacheRemoteContent))
		{
			var cont = new Ajax.Request(this.options.dataURL, {asynchronous: false, method: this.options.method});
			//
			// Expects the following XML format:
			// <HelpBalloon>
			// 		<title>My Title</title>
			// 		<content>My content</content>
			// </HelpBaloon>
			//
			var doHTML = false;
			if(cont.transport.responseXML)
			{
				var xml = cont.transport.responseXML.getElementsByTagName('HelpBalloon')[0];

				if(xml)
				{
					if(!this.options.title)
					{
						xmlTitle = xml.getElementsByTagName('title')[0];
						if(xmlTitle) this.title = xmlTitle.firstChild.nodeValue;
					}

					xmlContent = xml.getElementsByTagName('content')[0];
					if(xmlContent) this.options.content = xmlContent.firstChild.nodeValue;
				}
				else
					doHTML = true;
			}
			else
				doHTML = true;

			if(doHTML)
			{
				// Attempt to get the title from a <title/> HTML tag, unless the title option has been set. If so, use that.
				if(!this.options.title)
				{
					var htmlTitle = cont.transport.responseText.match(/\<title\>([^\<]+)\<\/title\>/gi);
					if(htmlTitle)
					{
						htmlTitle = htmlTitle.toString().replace(/\<title\>|\<\/title\>/gi, '');
						this.title = htmlTitle;
					}
				}
				this.options.content = cont.transport.responseText;
			}
		}
		
		this.balloonDimensions[0] = this.lastBalloon.width;
		this.balloonDimensions[1] = this.lastBalloon.height;
		
		var contentDimensions = [
			this.balloonDimensions[0] - (2 * this.options.contentMargin),
			this.balloonDimensions[1] - (2 * this.options.contentMargin)
		];
		
		var buttonDimensions = [
			this._elements.button.width,
			this._elements.button.height
		];
		
		//
		// Create all the elements on demand if they haven't been created yet
		//
		if(!this.drawn)
		{
			this._elements.inner = new Element('div');
		
			this._elements.title = new Element('div');
			this._elements.inner.appendChild(this._elements.title);
			
			// PNG fix for IE
			if(Browser.isMSIE() && this.options.button.toLowerCase().indexOf('.png') > -1)
			{
				this._elements.bgContainer = new Element('div');
				
				// Have to create yet-another-child of container to house the background for IE... when it was set in
				// the main container, it for some odd reason prevents child components from being clickable.
				this._elements.container.appendChild(this._elements.bgContainer);
				
				this._elements.closer =  new Element('div');
				this._elements.closer.setStyle('filter', 
					"progid:DXImageTransform.Microsoft.AlphaImageLoader(src='" + this.options.button + "', sizingMethod='scale')");
			}
			else
			{
				this._elements.closer = this._elements.button;
			}
			
			Event.observe(this._elements.closer, 'click', this.toggle.bindAsEventListener(this));
			this._elements.inner.appendChild(this._elements.closer);
			
			this._elements.content =  new Element('div');
			this._elements.inner.appendChild(this._elements.content);
			
			this._elements.container.appendChild(this._elements.inner);
			
			document.getElementsByTagName('body')[0].appendChild(this._elements.container);
			
			this.drawn = true;
		}

		// Reset the title element and reappend the title value (could have changed with a new URL)
		this._elements.title.innerHTML = '';
		this._elements.title.appendChild(document.createTextNode(this.title));
		
		// Reset content value:
		this._elements.content.innerHTML = this.options.content;

		//
		// Reapply styling to components as values might have changed
		//
		
		Element.setStyle(this._elements.inner, {
			'position': 	'absolute',
			'top':			this.options.contentMargin + 'px',
			'left':			this.options.contentMargin + 'px',
			'width': 		contentDimensions[0] + 'px',
			'height': 		contentDimensions[1] + 'px'
		});

		Element.setStyle(this._elements.title, {
			'width':		(contentDimensions[0] - buttonDimensions[0]) + 'px',
			'height':		buttonDimensions[1] + 'px',
			'position':		'absolute',
			'overflow':		'hidden',
			'top': 			'0px',
			'left': 		'0px'
		});
		
		Element.setStyle(this._elements.title, this.titleStyle);
		
		Element.setStyle(this._elements.closer, {
			'width': buttonDimensions[0] + 'px',
			'height': buttonDimensions[1] + 'px',
			'cursor': 	'pointer',
			'position':	'absolute',
			'top': 		'0px',
			'right': 	'0px'
		});
		
		Element.setStyle(this._elements.content, {
			'width':		contentDimensions[0] + 'px',
			'height': 		(contentDimensions[1] - this._elements.button.height) + 'px',
			'overflow': 	'auto',
			'position': 	'absolute',
			'top': 			buttonDimensions[1] + 'px',
			'left': 		'0px',
			'fontFamily': 	'verdana',
			'fontSize': 	'11px',
			'fontWeight': 	'normal',
			'color': 		'black'
		});
		
	},

	/**
	 * Gets the current position of the obj
	 * @param {Element} element to get position of
	 * @return Object of (x, y, x2, y2)
	 */
	_getXY: function(obj)
	{
		var pos = Position.cumulativeOffset(obj)
		var y = pos[1];
		var x = pos[0];
		var x2 = x + parseInt(obj.offsetWidth);
		var y2 = y + parseInt(obj.offsetHeight);
		return {'x':x, 'y':y, 'x2':x2, 'y2':y2};

	},

	/**
	 * Determins if the object is a child of the balloon element
	 * @param {Element} Element to check parentage
	 * @return {Boolean}
	 * @private
	 */
	_isChild: function(obj)
	{
		var i = 15;
		do{
			if(obj == this._elements.container)
				return true;
			obj = obj.parentNode;
		}while(obj && i--);
		return false
	},

	/**
	 * Determines if the balloon is over this_obj object
	 * @param {Element} Object to look under
	 * @return {Boolean}
	 * @private
	 */
	_isOver: function(this_obj)
	{
		if(!this.visible) return false;
		if(this_obj == this._elements.container || this._isChild(this_obj)) return false;
		var this_coords = this._getXY(this_obj);
		var that_coords = this._getXY(this._elements.container);
		if(
			(
			 (
			  (this_coords.x >= that_coords.x && this_coords.x <= that_coords.x2)
			   ||
			  (this_coords.x2 >= that_coords.x &&  this_coords.x2 <= that_coords.x2)
			 )
			 &&
			 (
			  (this_coords.y >= that_coords.y && this_coords.y <= that_coords.y2)
			   ||
			  (this_coords.y2 >= that_coords.y && this_coords.y2 <= that_coords.y2)
			 )
			)

		  ){
			return true;
		}
		else
			return false;
	},

	/**
	 * Restores visibility of elements under the balloon
	 * (For IE)
	 * TODO: suck yourself
	 * @private
	 */
	_showLowerElements: function()
	{
		if(this.options.hideUnderElementsInIE)
		{
			var elements = this._getWeirdAPIElements();
			for(var i = 0; i < elements.length; i++)
			{
				if(this._isOver(elements[i]))
				{
					if(elements[i].style.visibility != 'visible' && elements[i].hiddenBy == this)
					{
						elements[i].style.visibility = 'visible';
						elements[i].hiddenBy = null;
					}
				}
			}
		}
	},

	/**
	 * Hides elements below the balloon
	 * (For IE)
	 * @private
	 */
	_hideLowerElements: function()
	{
		if(this.options.hideUnderElementsInIE)
		{
			var elements = this._getWeirdAPIElements();
			for(var i = 0; i < elements.length; i++)
			{
				if(this._isOver(elements[i]))
				{
					if(elements[i].style.visibility != 'hidden')
					{
						elements[i].style.visibility = 'hidden';
						elements[i].hiddenBy = this;
					}
				}
			}
		}
	},

	/**
	 * Determines which elements need to be hidden
	 * (For IE)
	 * @return {Array} array of elements
	 */
	_getWeirdAPIElements: function()
	{
		if(!Browser.isMSIE()) return [];
		var objs = ['select', 'input', 'object'];
		var elements = [];
		for(var i = 0; i < objs.length; i++)
		{
			var e = document.getElementsByTagName(objs[i]);
			for(var j = 0; j < e.length; j++)
			{
				elements.push(e[j]);
			}
		}
		return elements;
	},

	/**
	 * Hides the other visible help balloons
	 * @param {Event} e
	 */
	_hideOtherHelps: function(e)
	{
		if(!e) e = window.event;
		var divs = document.getElementsByTagName('div');
		for(var i = 0; i < divs.length; i++)
		{
			if(divs[i]._HelpBalloon && divs[i]._HelpBalloon.visible && (divs[i] != this._elements.container))
				divs[i]._HelpBalloon.toggle(e);
		}
	}
};

/**
 * HelpBalloonOptions
 * Helper class for defining options for the HelpBalloon object
 * @author Beau D. Scott <beau_scott@hotmail.com>
 */
var HelpBalloonOptions = Class.create();
HelpBalloonOptions.prototype = {
	/**
	 * @constructor
	 */
	initialize: function(){},
	/**
	 * For use with embedding this object into another. If true, the icon is not created
	 * and not appeneded to the DOM at construction.
	 * Default is false
	 * @var {Boolean}
	 */
	returnElement: false,
	/**
	 * URL to the anchoring icon image file to use. This can also be a direct reference 
	 * to an existing element if you're using that as your anchoring icon.
	 * @var {Object}
	 */
	icon: '/accounts/static/images/balloons/icon.gif',
	/**
	 * Alt text of the help icon
	 * @var {String}
	 */
	altText: 'Click here for help with this topic.',
	/**
	 * URL to pull the title/content XML
	 * @var {String}
	 */
	dataURL: null,
	/**
	 * Static title of the balloon
	 * @var {String}
	 */
	title: null,
	/**
	 * Static content of the balloon
	 * @var {String}
	 */
	content: null,
	/**
	 * Show/Hide effect duration
	 * @var {Number}
	 */
	duration: 0.2,
	/**
	 * The event type to listen for on the icon to show the balloon.
	 * Default 'click'
	 * @var {String}
	 */
	useEvent: ['click'],
	/**
	 * Request method for dynamic content. (get, post)
	 * Default 'get'
	 * @var {String}
	 */
	method:	'get',
	/**
	 * Flag indicating cache the request result. If this is false, every
	 * time the balloon is shown, it will retrieve the remote url and parse it
	 * before the balloon appears, updating the content. Otherwise, it will make
	 * the call once and use the same content with each subsequent showing.
	 * Default true
	 * @var {Boolean}
	 */
	cacheRemoteContent: true,
	/**
	 * Vertical and horizontal margin of the content pane
	 * @var {Number}
	 */
	contentMargin: 35,
	/**
	 * X coordinate of the closing button
	 * @var {Number}
	 */
	buttonX: 246,
	/**
	 * Y coordinate of the closing button
	 * @var {Number}
	 */
	buttonY: 35,
	/**
	 * Clossing button image path
	 * @var {String}
	 */
	button: '/accounts/static/images/balloons/button.png',
	/**
	 * Balloon image path prefix. There are 4 button images, numerically named, starting with 0.
	 * 0, 1
	 * 2, 3
	 * (the number indicates the corner opposite the anchor (the pointing direction)
	 * @var {String}
	 */
	balloonPrefix: '/accounts/static/images/balloons/balloon-',
	/**
	 * The image filename suffix, including the file extension
	 * @var {String}
	 */
	balloonSuffix: '.png',
	/**
	 * Position of the balloon's anchor relative to the icon element.
	 * Combine one horizontal indicator (left, center, right) and one vertical indicator (top, middle, bottom).
	 * Default is 'center middle'
	 * @var {String}
	 */
	anchorPosition: 'center middle',
	/**
	 * Flag indicating whether to hide the elements under the balloon in IE.
	 * Setting this to false can cause rendering issues in Internet Explorer
	 * as some elements appear on top of the balloon if they're not hidden.
	 * Default is true.
	 * @var {Boolean}
	 */
	hideUnderElementsInIE: true
};

/**
 * HelpBalloonElements
 * Helper class for defining elements for the HelpBalloon object
 * @author Beau D. Scott <beau_scott@hotmail.com>
 */
var HelpBalloonElements = Class.create();
HelpBalloonElements.prototype = {
	/**
	 * @constructor
	 */
	initialize: function(){},
	/**
	 * Containing element of the balloon
	 * @var {Element}
	 */
	container: null,
	/**
	 * Inner content container
	 * @var {Element}
	 */
	inner: null,
	/**
	 * A reference to the anchoring element/icon
	 * @var {Element}
	 */
	icon: null,
	/**
	 * Content container
	 * @var {Element}
	 */
	content: null,
	/**
	 * Closing button element
	 * @var {Element}
	 */
	button: null,
	/**
	 * The closer object. This can be the same as button, but could 
	 * also be a div with a png loaded as the back ground, browser dependent.
	 * @var {Element}
	 */
	closer: null,
	/**
	 * Title container
	 * @var {Element}
	 */
	title: null,
	/**
	 * Background container (houses the balloon images
	 * @var {Element}
	 */
	bgContainer: null,
	/**
	 * Array of balloon image references
	 * @var {Array}
	 */
	balloons: []
};
