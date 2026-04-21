def get_stylesheet(theme_name, palette):
    acc = palette["accent"]
    glow = palette["glow"]

    return f"""
        #mainContainer {{
            background-color: #0b0c10;
            background: qradialgradient(cx:0.5, cy:0.5, radius:1.2, fx:0.5, fy:0.5, stop:0 #1a1c2c, stop:1 #0b0c10);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 10);
        }}
        
        #titleBar {{
            background-color: rgba(255, 255, 255, 4);
            border-bottom: 1px solid rgba(255, 255, 255, 8);
            border-top-left-radius: 16px;
            border-top-right-radius: 16px;
        }}
        
        #appTitle {{
            font-size: 18px;
            font-weight: 900;
            color: white;
            letter-spacing: 7px;
            padding-left: 10px;
        }}
        
        /* New Underlined Tab Selector */
        #modePill {{
            background-color: transparent;
            border: none;
        }}
        
        #pillBtn {{
            background-color: transparent;
            color: rgba(255, 255, 255, 80);
            font-weight: 800;
            font-size: 11px;
            padding: 10px 5px;
            margin: 0 15px;
            border: none;
            border-bottom: 3px solid transparent;
            letter-spacing: 2px;
            text-transform: uppercase;
        }}
        
        #pillBtn:checked {{
            color: white;
            border-bottom: 3px solid {acc};
        }}
        
        #pillBtn:hover:not(:checked) {{
            color: rgba(255, 255, 255, 150);
            border-bottom: 3px solid rgba(255, 255, 255, 20);
        }}
        
        #winCtrlBtn, #winCtrlBtnClose {{
            background-color: transparent;
            color: rgba(255, 255, 255, 180);
            font-size: 14px;
            border-radius: 10px;
            width: 32px;
            height: 32px;
        }}
        #winCtrlBtn:hover {{ background-color: rgba(255, 255, 255, 10); color: white; }}
        #winCtrlBtnClose:hover {{ background-color: #ef233c; color: white; }}

        #glassPanel {{
            background-color: rgba(255, 255, 255, 6);
            border: 1px solid rgba(255, 255, 255, 10);
            border-top: 1px solid rgba(255, 255, 255, 20);
            border-radius: 28px;
        }}
        
        #headerLabel {{
            font-size: 11px;
            font-weight: 900;
            color: white;
            letter-spacing: 3px;
            text-transform: uppercase;
            padding-bottom: 6px;
            border-bottom: 2px solid {acc};
        }}
        
        QLabel {{ color: rgba(255, 255, 255, 180); font-size: 12px; font-weight: 600; }}
        
        #queueList {{
            background: transparent;
            border: none;
            outline: none;
        }}
        #queueList::item {{
            background-color: rgba(255, 255, 255, 6);
            border-radius: 16px;
            padding: 15px;
            margin-bottom: 12px;
            color: rgba(255, 255, 255, 200);
            font-weight: 700;
            border: 1px solid transparent;
        }}
        #queueList::item:selected {{
            background-color: {glow};
            color: white;
            border: 1px solid {acc};
        }}

        QLineEdit, QComboBox {{
            background-color: rgba(0, 0, 0, 140);
            border: 1px solid rgba(255, 255, 255, 12);
            border-radius: 14px;
            padding: 12px 18px;
            color: white;
            font-size: 13px;
        }}
        QLineEdit:focus {{ border: 1.5px solid {acc}; background-color: rgba(0,0,0,180); }}
        
        #browseBtn {{
            background-color: rgba(255, 255, 255, 10);
            border-radius: 14px;
            color: white;
            font-size: 18px;
            border: 1px solid rgba(255,255,255,5);
        }}
        #browseBtn:hover {{ background-color: {acc}; border: 1px solid white; }}

        #startBtn {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {acc}, stop:1 #4361ee);
            color: white; font-weight: 900; padding: 20px; border-radius: 20px;
            text-transform: uppercase; letter-spacing: 4px; font-size: 14px;
            margin-top: 10px;
            border: 1px solid rgba(255, 255, 255, 20);
        }}
        #startBtn:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {acc}, stop:1 #4cc9f0);
            box-shadow: 0 0 25px {glow};
            border: 1px solid white;
        }}

        #secondaryBtn {{
            background-color: rgba(255, 255, 255, 8);
            border: 1px solid rgba(255, 255, 255, 12);
            color: rgba(255, 255, 255, 220); font-weight: 800; padding: 12px 20px; border-radius: 14px;
            font-size: 10px; letter-spacing: 1.5px;
        }}
        #secondaryBtn:hover {{ background-color: {glow}; border-color: {acc}; color: white; }}

        #abortBtn {{
            background-color: transparent; border: 2px solid rgba(247, 37, 133, 100);
            color: #f72585; padding: 16px; border-radius: 20px; font-weight: 900;
            text-transform: uppercase; font-size: 11px; letter-spacing: 2px;
        }}
        #abortBtn:hover {{ background-color: rgba(247, 37, 133, 20); border-color: #f72585; }}

        #logDisplay {{
            background-color: rgba(0, 0, 0, 180); 
            border-radius: 24px;
            color: #4cc9f0; font-family: 'Consolas', 'Cascadia Code', monospace; font-size: 11px;
            padding: 20px; border: 1px solid rgba(255, 255, 255, 8);
        }}

        QProgressBar {{
            border: none; border-radius: 6px; background-color: rgba(255, 255, 255, 5); height: 12px;
            text-align: center; color: transparent;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {acc}, stop:1 #4cc9f0);
            border-radius: 6px;
        }}
        
        #statusLabel {{ color: {acc}; font-weight: 900; font-size: 13px; margin-top: 10px; letter-spacing: 1px; }}
        
        #iconBtn {{ 
            background-color: rgba(255, 255, 255, 8); 
            border-radius: 12px; 
            color: white; 
            font-size: 18px;
            border: 1px solid rgba(255,255,255,10);
        }}
        #iconBtn:hover {{ background-color: {acc}; border-color: white; }}

        QScrollBar:vertical {{ border: none; background: transparent; width: 4px; margin: 0px; }}
        QScrollBar::handle:vertical {{ background: rgba(255, 255, 255, 10); min-height: 20px; border-radius: 2px; }}
        QScrollBar::handle:vertical:hover {{ background: {acc}; }}
    """

THEMES = {
    "Blue": {"accent": "#4cc9f0", "glow": "rgba(76, 201, 240, 40)"},
    "Pink": {"accent": "#f72585", "glow": "rgba(247, 37, 133, 40)"},
    "Green": {"accent": "#06d6a0", "glow": "rgba(6, 214, 160, 40)"},
    "Orange": {"accent": "#fb8500", "glow": "rgba(251, 133, 0, 40)"},
    "Purple": {"accent": "#7209b7", "glow": "rgba(114, 9, 183, 40)"}
}
