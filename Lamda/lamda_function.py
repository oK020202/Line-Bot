import logging
import os
import io
import urllib.request
import json
import datetime
from dateutil.relativedelta import relativedelta
import boto3
from PIL import Image, ImageDraw, ImageFont

import data_function # DynamoDBに送信するための関数のパッケージ
import image_function # S3と画像をやり取りするための関数パッケージ

# ログ取得の設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 推奨グレード画像
grade_info_image = "Ref Image Link"


"""
テスト画像(S3)
"""
testimage = "Test Image Link"

"""
自治体名ID・がんID
"""
city_list = ["大阪市", "堺市", "岸和田市", "豊中市", "池田市", "吹田市", "泉大津市", "高槻市", "貝塚市", "守口市", "枚方市", "茨木市", "八尾市", "泉佐野市", "富田林市", "寝屋川市", "河内長野市", "松原市", "大東市", "和泉市", "箕面市", "柏原市", "羽曳野市", "門真市", "摂津市", "高石市", "藤井寺市", "東大阪市", "泉南市", "四條畷市", "交野市", "大阪狭山市", "阪南市", "島本町", "豊能町", "能勢町", "忠岡町", "熊取町", "田尻町", "岬町", "太子町", "河南町", "千早赤阪村"]
cancer_list = ['胃がん', '肺がん', '大腸がん', '乳がん', '子宮けいがん', '前立腺がん', '口腔がん']

"""
メッセージ定義
"""
follow_message_text = {
                "type": "text",
                "text": "自治体で受けられるがん検診をお知らせします $",
                "emojis":[
                    {
                        "index": 22,
                        "productId": "5ac21542031a6752fb806d55",
                        "emojiId": "224"
                    }
                ]
            }
            
delete_text = {
                "type": "text",
                "text": "登録した情報を削除するには、このアカウントをブロックするかして下さい。(ブロック解除した際には再度の登録が必要です。)",
            }
            
sorry_text = {
                "type": "text",
                "text": "申し訳ございませんが、個別のメッセージには対応しておりません $",
                "emojis":[
                    {
                        "index": 31,
                        "productId": "5ac21e6c040ab15980c9b444",
                        "emojiId": "039"
                    }
                ]
            }
            
birth_ask_flex = {
              "type":"flex",
              "altText": "[登録1/3]誕生日を教えてください",
              "contents": 
                {
                  "type": "bubble",
                  "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                      {
                        "type": "text",
                        "text": "[登録1/3]誕生日を教えてください",
                        "weight": "bold"
                      }
                    ],
                    "backgroundColor": "#EEEEEE",
                    "paddingTop": "15px",
                    "paddingBottom": "15px"
                  },
                  "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                      {
                        "type": "button",
                        "action": {
                          "type": "datetimepicker",
                          "label": "入力する",
                          "data": "birth",
                          "mode": "date",
                          "initial": "2000-01-01",
                          "min": "1920-01-01",
                          "max": "2021-12-31"
                        },
                        "style": "primary"
                      }
                    ]
                  }
                }
            }
            
sex_ask_buble = {
              "type": "flex",
              "altText": "[登録2/3]性別を教えてください",
              "contents": 
                {
                  "type": "bubble",
                  "size": "kilo",
                  "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                      {
                        "type": "text",
                        "text": "[登録2/3]性別を教えてください",
                        "align": "center",
                        "weight": "bold"
                      }
                    ],
                    "backgroundColor": "#EEEEEE"
                  },
                  "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                      {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                          {
                            "type": "button",
                            "action": {
                              "type": "postback",
                              "label": "女",
                              "data": "gender, 1",
                              "displayText": "女"
                            },
                            "style": "primary"
                          },
                          {
                            "type": "button",
                            "action": {
                              "type": "postback",
                              "label": "男",
                              "data": "gender, 0",
                              "displayText": "男"
                            },
                            "style": "primary",
                            "margin": "10px"
                          }
                        ]
                      },
                      {
                        "type": "button",
                        "action": {
                          "type": "postback",
                          "label": "性別を選択しない",
                          "data": "gender, 3",
                          "displayText": "性別を選択しない"
                        },
                        "margin": "5px"
                      }
                    ],
                    "height": "130px"
                  }
                }
               
          }

birth_save_text = {
                "type": "text",
                "text": "誕生日を登録しました", #postback_event["postback"]["params"]["date"]
            }
            
"""
area_ask_flex = {
              "type": "flex",
              "altText": "this is a flex message",
              "contents": 
                {
                  "type": "bubble",
                  "size": "giga",
                  "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                      {
                        "type": "text",
                        "text": "[登録3/3]お住みの地域を教えてください",
                        "align": "center",
                        "weight": "bold"
                      }
                    ],
                    "backgroundColor": "#EEEEEE"
                  },
                  "body": {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                      {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                          {
                            "type": "button",
                            "action": {
                              "type": "message",
                              "label": "大阪市",
                              "text": "大阪市"
                            },
                            "style": "primary",
                            "margin": "5px"
                          },
                          {
                            "type": "button",
                            "action": {
                              "type": "message",
                              "label": "豊能地区",
                              "text": "豊能地区"
                            },
                            "style": "primary",
                            "margin": "5px"
                          },
                          {
                            "type": "button",
                            "action": {
                              "type": "message",
                              "label": "北河内地区",
                              "text": "北河内地区"
                            },
                            "style": "primary",
                            "margin": "5px"
                          },
                          {
                            "type": "button",
                            "action": {
                              "type": "message",
                              "label": "泉北地区",
                              "text": "泉北地区"
                            },
                            "style": "primary",
                            "margin": "5px"
                          },
                          {
                            "type": "button",
                            "action": {
                              "type": "message",
                              "label": "南河内地区",
                              "text": "南河内地区"
                            },
                            "style": "primary",
                            "margin": "5px"
                          }
                        ],
                        "offsetEnd": "5px"
                      },
                      {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                          {
                            "type": "button",
                            "action": {
                              "type": "message",
                              "label": "堺市",
                              "text": "堺市"
                            },
                            "style": "primary",
                            "margin": "5px"
                          },
                          {
                            "type": "button",
                            "action": {
                              "type": "message",
                              "label": "三島地区",
                              "text": "三島地区"
                            },
                            "style": "primary",
                            "margin": "5px"
                          },
                          {
                            "type": "button",
                            "action": {
                              "type": "message",
                              "label": "中河内地区",
                              "text": "中河内地区"
                            },
                            "style": "primary",
                            "margin": "5px"
                          },
                          {
                            "type": "button",
                            "action": {
                              "type": "message",
                              "label": "泉南地区",
                              "text": "泉南地区"
                            },
                            "style": "primary",
                            "margin": "5px"
                          }
                        ]
                      }
                    ]
                  }
                }
            }

city_ask_minamikawachi = {
              "type": "flex",
              "altText": "this is a flex message",
              "contents": 
                {
                  "type": "bubble",
                  "size": "giga",
                  "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                      {
                        "type": "text",
                        "text": "[登録3/3]住民票のある自治体を教えてください",
                        "align": "center",
                        "weight": "bold"
                      },
                      {
                        "type": "text",
                        "text": "南河内地区："
                      }
                    ],
                    "backgroundColor": "#EEEEEE",
                    "height": "70px"
                  },
                  "body": {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                      {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                          {
                            "type": "button",
                            "action": {
                              "type": "postback",
                              "label": "松原市",
                              "data": "松原市",
                              "displayText": "松原市"
                            },
                            "style": "primary",
                            "margin": "5px"
                          },
                          {
                            "type": "button",
                            "action": {
                              "type": "message",
                              "label": "藤井寺市",
                              "text": "藤井寺市"
                            },
                            "style": "primary",
                            "margin": "5px"
                          },
                          {
                            "type": "button",
                            "action": {
                              "type": "message",
                              "label": "河南町",
                              "text": "河南町"
                            },
                            "style": "primary",
                            "margin": "5px"
                          },
                          {
                            "type": "button",
                            "action": {
                              "type": "message",
                              "label": "富田林市",
                              "text": "富田林市"
                            },
                            "style": "primary",
                            "margin": "5px"
                          },
                          {
                            "type": "button",
                            "action": {
                              "type": "message",
                              "label": "河内長野市",
                              "text": "河内長野市"
                            },
                            "style": "primary",
                            "margin": "5px"
                          }
                        ],
                        "offsetEnd": "5px"
                      },
                      {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                          {
                            "type": "button",
                            "action": {
                              "type": "message",
                              "label": "羽曳野市",
                              "text": "羽曳野市"
                            },
                            "style": "primary",
                            "margin": "5px"
                          },
                          {
                            "type": "button",
                            "action": {
                              "type": "message",
                              "label": "太子町",
                              "text": "太子町"
                            },
                            "style": "primary",
                            "margin": "5px"
                          },
                          {
                            "type": "button",
                            "action": {
                              "type": "message",
                              "label": "千早赤阪村",
                              "text": "千早赤阪村"
                            },
                            "style": "primary",
                            "margin": "5px"
                          },
                          {
                            "type": "button",
                            "action": {
                              "type": "message",
                              "label": "大阪狭山市",
                              "text": "大阪狭山市"
                            },
                            "style": "primary",
                            "margin": "5px"
                          },
                          {
                            "type": "button",
                            "action": {
                              "type": "postback",
                              "label": "地域選択に戻る",
                              "data": "地域選択に戻る",
                              "displayText": "地域選択に戻る"
                            },
                            "margin": "5px"
                          }
                        ]
                      }
                    ]
                  }
                }
            }
"""
            
city_ask_carousel = {
              "type":"flex",
              "altText": "[登録3/3]住民票のある自治体を教えてください",
              "contents": 
                {
                  "type": "carousel",
                  "contents": [
                    {
                      "type": "bubble",
                      "size": "giga",
                      "header": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                          {
                            "type": "text",
                            "text": "[登録3/3]住民票のある自治体を\n教えてください",
                            "weight": "bold",
                            "wrap": True,
                            "gravity": "top"
                          }
                        ],
                        "backgroundColor": "#EEEEEE",
                        "paddingTop": "12px",
                        "paddingBottom": "12px"
                      },
                      "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                          {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                              {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "大阪市",
                                      "data": "localgov, 0",
                                      "displayText": "大阪市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "東大阪市",
                                      "data": "localgov, 27",
                                      "displayText": "東大阪市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "豊中市",
                                      "data": "localgov, 3",
                                      "displayText": "豊中市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "吹田市",
                                      "data": "localgov, 5",
                                      "displayText": "吹田市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "八尾市",
                                      "data": "localgov, 12",
                                      "displayText": "八尾市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  }
                                ]
                              },
                              {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "堺市",
                                      "data": "localgov, 1",
                                      "displayText": "堺市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "枚方市",
                                      "data": "localgov, 10",
                                      "displayText": "枚方市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "高槻市",
                                      "data": "localgov, 7",
                                      "displayText": "高槻市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "茨木市",
                                      "data": "localgov, 11",
                                      "displayText": "茨木市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "寝屋川市",
                                      "data": "localgov, 15",
                                      "displayText": "寝屋川市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  }
                                ],
                                "margin": "5px"
                              }
                            ]
                          }
                        ],
                        "paddingTop": "15px"
                      }
                    },
                    {
                      "type": "bubble",
                      "size": "giga",
                      "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                          {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                              {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "岸和田市",
                                      "data": "localgov, 2",
                                      "displayText": "岸和田市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "守口市",
                                      "data": "localgov, 9",
                                      "displayText": "守口市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "箕面市",
                                      "data": "localgov, 20",
                                      "displayText": "箕面市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "松原市",
                                      "data": "localgov, 17",
                                      "displayText": "松原市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "羽曳野市",
                                      "data": "localgov, 22",
                                      "displayText": "羽曳野市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "池田市",
                                      "data": "localgov, 4",
                                      "displayText": "池田市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  }
                                ]
                              },
                              {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "和泉市",
                                      "data": "localgov, 19",
                                      "displayText": "和泉市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "門真市",
                                      "data": "localgov, 23",
                                      "displayText": "門真市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "大東市",
                                      "data": "localgov, 18",
                                      "displayText": "大東市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "富田林市",
                                      "data": "localgov, 14",
                                      "displayText": "富田林市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "河内長野市",
                                      "data": "localgov, 16",
                                      "displayText": "河内長野市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "泉佐野市",
                                      "data": "localgov, 13",
                                      "displayText": "泉佐野市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  }
                                ],
                                "margin": "5px"
                              }
                            ]
                          }
                        ]
                      }
                    },
                    {
                      "type": "bubble",
                      "size": "giga",
                      "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                          {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                              {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "貝塚市",
                                      "data": "localgov, 8",
                                      "displayText": "貝塚市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "交野市",
                                      "data": "localgov, 30",
                                      "displayText": "交野市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "柏原市",
                                      "data": "localgov, 21",
                                      "displayText": "柏原市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "大阪狭山市",
                                      "data": "localgov, 31",
                                      "displayText": "大阪狭山市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "阪南市",
                                      "data": "localgov, 32",
                                      "displayText": "阪南市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "摂津市",
                                      "data": "localgov, 24",
                                      "displayText": "摂津市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  }
                                ],
                                "margin": "5px"
                              },
                              {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "泉大津市",
                                      "data": "localgov, 6",
                                      "displayText": "泉大津市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "藤井寺市",
                                      "data": "localgov, 26",
                                      "displayText": "藤井寺市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "高石市",
                                      "data": "localgov, 25",
                                      "displayText": "高石市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "島本町",
                                      "data": "localgov, 33",
                                      "displayText": "島本町"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "四條畷市",
                                      "data": "localgov, 29",
                                      "displayText": "四條畷市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "熊取町",
                                      "data": "localgov, 37",
                                      "displayText": "熊取町"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  }
                                ]
                              }
                            ]
                          }
                        ]
                      }
                    },
                    {
                      "type": "bubble",
                      "size": "giga",
                      "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                          {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                              {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "泉南市",
                                      "data": "localgov, 28",
                                      "displayText": "泉南市"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "忠岡町",
                                      "data": "localgov, 36",
                                      "displayText": "忠岡町"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "河南町",
                                      "data": "localgov, 41",
                                      "displayText": "河南町"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "能勢町",
                                      "data": "localgov, 35",
                                      "displayText": "能勢町"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "千早赤阪村",
                                      "data": "42",
                                      "displayText": "千早赤阪村"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  }
                                ]
                              },
                              {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "豊能町",
                                      "data": "localgov, 34",
                                      "displayText": "豊能町"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "岬町",
                                      "data": "localgov, 39",
                                      "displayText": "岬町"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "太子町",
                                      "data": "localgov, 40",
                                      "displayText": "太子町"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  },
                                  {
                                    "type": "button",
                                    "action": {
                                      "type": "postback",
                                      "label": "田尻町",
                                      "data": "localgov, 38",
                                      "displayText": "田尻町"
                                    },
                                    "style": "primary",
                                    "margin": "5px"
                                  }
                                ],
                                "margin": "5px"
                              }
                            ]
                          }
                        ]
                      }
                    }
                  ]
                }
            }
            
select_edit = {
              "type":"flex",
              "altText": "登録情報の変更/削除",
              "contents": 
                {
                  "type": "bubble",
                  "size": "kilo",
                  "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                      {
                        "type": "text",
                        "text": "登録情報の変更/削除",
                        "align": "center",
                        "weight": "bold"
                      }
                    ],
                    "backgroundColor": "#EEEEEE"
                  },
                  "body": {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                      {
                        "type": "button",
                        "action": {
                          "type": "postback",
                          "label": "再登録",
                          "data": "data, edit",
                          "displayText": "再登録"
                        },
                        "style": "primary"
                      },
                      {
                        "type": "button",
                        "action": {
                          "type": "postback",
                          "label": "削除",
                          "data": "data, delete",
                          "displayText": "削除"
                        },
                        "style": "primary",
                        "margin": "10px"
                      }
                    ]
                  }
                }
            }
            
genderless_ask_bubble = {
              "type":"flex",
              "altText": "性別を選択しない場合は男女両方のがん検診を通知します",
              "contents": 
                {
                  "type": "bubble",
                  "size": "mega",
                  "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                      {
                        "type": "text",
                        "text": "性別を選択しない場合は男女両方の\nがん検診を通知します",
                        "align": "center",
                        "weight": "bold",
                        "wrap": True
                      }
                    ],
                    "backgroundColor": "#EEEEEE"
                  },
                  "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                      {
                        "type": "button",
                        "action": {
                          "type": "postback",
                          "label": "了解しました",
                          "data": "gender, 2",
                          "displayText": "了解しました"
                        },
                        "style": "primary"
                      },
                      {
                        "type": "button",
                        "action": {
                          "type": "postback",
                          "label": "性別選択に戻る",
                          "data": "select, gender",
                          "displayText": "性別選択に戻る"
                        },
                        "margin": "5px"
                      }
                    ],
                    "height": "140px"
                  }
                }
            }

                        

            
"""
メッセージ定義
"""
follow_message_message = [
            follow_message_text,
            birth_ask_flex
        ]
        
birth_ask_message = [
            birth_ask_flex,
        ]

birth_save_message = [
            birth_save_text,
            sex_ask_buble
        ]
        
sex_ask_message = [
            sex_ask_buble
        ]


"""
登録時のメッセージ送信
"""
def follow_message(event):
    logger.info(json.dumps(event))
    """
        ユーザーIDデータの格納の処理を描く
    """
    user_id = event["source"]["userId"]
    print("User ID:", user_id)
    data_function.put_data(user_id) 
    """
    LINE APIとのやりとり
    """
    # POSTリクエストの準備(返信)
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        'Authorization': 'Bearer ' + os.environ['ACCESSTOKEN']
    }
    data = {
        "replyToken": event["replyToken"],
        "messages": follow_message_message
    }
    # POSTリクエスト
    req = urllib.request.Request(url=url, data=json.dumps(data).encode("utf-8"), method="POST", headers=headers)
    
    with urllib.request.urlopen(req) as res:
        
        logger.info(res.read().decode("utf-8"))
        
        return {
            "statusCode": 200,
            "body": json.dumps("Hello from Lambda!")
        }
        
"""
誕生日を聞く
"""
def birthday_ask(message_event):
    logger.info(json.dumps(message_event))
    
    # POSTリクエストの準備(返信)
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        'Authorization': 'Bearer ' + os.environ['ACCESSTOKEN']
    }
    data = {
        "replyToken": message_event["replyToken"],
        "messages": birth_ask_message
    }
    # 返信メッセージの送信(POSTリクエスト)
    req = urllib.request.Request(url=url, data=json.dumps(data).encode("utf-8"), method="POST", headers=headers)
    
    with urllib.request.urlopen(req) as res:
        
        logger.info(res.read().decode("utf-8"))
        
        return {
            "statusCode": 200,
            "body": json.dumps("Hello from Lambda!")
        }
  
"""
誕生日の格納
"""
def birth_save(event):
    logger.info(json.dumps(event))
    """
        誕生日データの格納の処理を描く
    """
    user_id = event["source"]["userId"]
    birthday = event["postback"]["params"]["date"]
    print("User ID:", user_id, ", Birthday:", birthday)
    data_function.modify_data(user_id, birthday = birthday) #DBに送信
    
    """
    LINE APIとのやりとり
    """
    # データの送信
    # POSTリクエストの準備(返信)
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        'Authorization': 'Bearer ' + os.environ['ACCESSTOKEN']
    }
    data = {
        "replyToken": event["replyToken"],
        "messages": birth_save_message
    }
    # 返信メッセージの送信(POSTリクエスト)
    req = urllib.request.Request(url=url, data=json.dumps(data).encode("utf-8"), method="POST", headers=headers)
    
    with urllib.request.urlopen(req) as res:
        
        logger.info(res.read().decode("utf-8"))
        
        return {
            "statusCode": 200,
            "body": json.dumps("Hello from Lambda!")
        }
    
## 性別の選択
def sex_ask(event):
    logger.info(json.dumps(event))
    
    # POSTリクエストの準備(返信)
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        'Authorization': 'Bearer ' + os.environ['ACCESSTOKEN']
    }
    data = {
        "replyToken": event["replyToken"],
        "messages": sex_ask_message
    }
    # 返信メッセージの送信(POSTリクエスト)
    req = urllib.request.Request(url=url, data=json.dumps(data).encode("utf-8"), method="POST", headers=headers)
    
    with urllib.request.urlopen(req) as res:
        
        logger.info(res.read().decode("utf-8"))
        
        return {
            "statusCode": 200,
            "body": json.dumps("Hello from Lambda!")
        }


## 性別の保存・自治体を聞く
def gender_save(event):
    logger.info(json.dumps(event))
    """
        誕生日データの格納の処理を描く
    """
    user_id = event["source"]["userId"]
    sex = event["postback"]["data"].split(", ")[1]
    print("User ID:", user_id, ", Sex:", sex)
    data_function.modify_data(user_id, sex = int(sex)) #性別:男 #DBに送信
    
    """
    LINE APIとのやりとり
    """
    # POSTリクエストの準備(返信)
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        'Authorization': 'Bearer ' + os.environ['ACCESSTOKEN']
    }
    data = {
        "replyToken": event["replyToken"],
        "messages": [city_ask_carousel]
    }
    # 返信メッセージの送信(POSTリクエスト)
    req = urllib.request.Request(url=url, data=json.dumps(data).encode("utf-8"), method="POST", headers=headers)
    
    with urllib.request.urlopen(req) as res:
        
        logger.info(res.read().decode("utf-8"))
        
        return {
            "statusCode": 200,
            "body": json.dumps("Hello from Lambda!")
        }

        

        
## 居住地の選択
def city_ask(message_event):
    # POSTリクエストの準備(返信)
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        'Authorization': 'Bearer ' + os.environ['ACCESSTOKEN']
    }
    data = {
        "replyToken": message_event["replyToken"],
        "messages": [city_ask_carousel]
    }
    # 返信メッセージの送信(POSTリクエスト)
    req = urllib.request.Request(url=url, data=json.dumps(data).encode("utf-8"), method="POST", headers=headers)
    
    with urllib.request.urlopen(req) as res:
        logger.info(res.read().decode("utf-8"))
        return {
            "statusCode": 200,
            "body": json.dumps("Hello from Lambda!")
        }
        
        
#登録情報の編集・削除が押された時に編集か削除を選ばせる
def data_edit(events):
  # POSTリクエストの準備(返信)
  url = "https://api.line.me/v2/bot/message/reply"
  headers = {
      "Content-Type": "application/json",
      'Authorization': 'Bearer ' + os.environ['ACCESSTOKEN']
  }
  data = {
      "replyToken": events["replyToken"],
      "messages": [select_edit]
  }
  # 返信メッセージの送信(POSTリクエスト)
  req = urllib.request.Request(url=url, data=json.dumps(data).encode("utf-8"), method="POST", headers=headers)
  
  with urllib.request.urlopen(req) as res:
        logger.info(res.read().decode("utf-8"))
  return {
            "statusCode": 200,
            "body": json.dumps("Hello from Lambda!")
        }


# その他のメッセージに対して、個別対応はしていない旨を伝える
def send_sorry(events):
  # POSTリクエストの準備(返信)
  url = "https://api.line.me/v2/bot/message/reply"
  headers = {
      "Content-Type": "application/json",
      'Authorization': 'Bearer ' + os.environ['ACCESSTOKEN']
  }
  data = {
      "replyToken": events["replyToken"],
      "messages": [sorry_text]
  }
  # 返信メッセージの送信(POSTリクエスト)
  req = urllib.request.Request(url=url, data=json.dumps(data).encode("utf-8"), method="POST", headers=headers)
  
  with urllib.request.urlopen(req) as res:
        logger.info(res.read().decode("utf-8"))
  return {
            "statusCode": 200,
            "body": json.dumps("Hello from Lambda!")
        }
        


# 性別未選択の確認メッセージ送信
def genderless_ask(events):
   # POSTリクエストの準備(返信)
  url = "https://api.line.me/v2/bot/message/reply"
  headers = {
      "Content-Type": "application/json",
      'Authorization': 'Bearer ' + os.environ['ACCESSTOKEN']
  }
  data = {
      "replyToken": events["replyToken"],
      "messages": [genderless_ask_bubble]
  }
  # 返信メッセージの送信(POSTリクエスト)
  req = urllib.request.Request(url=url, data=json.dumps(data).encode("utf-8"), method="POST", headers=headers)
  
  with urllib.request.urlopen(req) as res:
        logger.info(res.read().decode("utf-8"))
  return {
            "statusCode": 200,
            "body": json.dumps("Hello from Lambda!")
        }
        
# 性別選択の確認メッセージを再送
def reselect_gender(events):
   # POSTリクエストの準備(返信)
  url = "https://api.line.me/v2/bot/message/reply"
  headers = {
      "Content-Type": "application/json",
      'Authorization': 'Bearer ' + os.environ['ACCESSTOKEN']
  }
  data = {
      "replyToken": events["replyToken"],
      "messages": [sex_ask_buble]
  }
  # 返信メッセージの送信(POSTリクエスト)
  req = urllib.request.Request(url=url, data=json.dumps(data).encode("utf-8"), method="POST", headers=headers)
  
  with urllib.request.urlopen(req) as res:
        logger.info(res.read().decode("utf-8"))
  return {
            "statusCode": 200,
            "body": json.dumps("Hello from Lambda!")
        }

# 情報の再登録
def reregister(event):
    logger.info(json.dumps(event))
    # POSTリクエストの準備(返信)
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        'Authorization': 'Bearer ' + os.environ['ACCESSTOKEN']
    }
    data = {
        "replyToken": event["replyToken"],
        "messages": [birth_ask_flex]
    }
    # POSTリクエスト
    req = urllib.request.Request(url=url, data=json.dumps(data).encode("utf-8"), method="POST", headers=headers)
    
    with urllib.request.urlopen(req) as res:
        
        logger.info(res.read().decode("utf-8"))
        
        return {
            "statusCode": 200,
            "body": json.dumps("Hello from Lambda!")
        }
        
# 登録情報の削除について
def delete_request(event):
    logger.info(json.dumps(event))
    # POSTリクエストの準備(返信)
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        'Authorization': 'Bearer ' + os.environ['ACCESSTOKEN']
    }
    data = {
        "replyToken": event["replyToken"],
        "messages": [delete_text]
    }
    # POSTリクエスト
    req = urllib.request.Request(url=url, data=json.dumps(data).encode("utf-8"), method="POST", headers=headers)
    
    with urllib.request.urlopen(req) as res:
        
        logger.info(res.read().decode("utf-8"))
        
        return {
            "statusCode": 200,
            "body": json.dumps("Hello from Lambda!")
        }
        
# jsonデータからのデータ抽出
def data_extract(user_info, result_one, genderless=0):
    # 自治体
    address = city_list[int(user_info["Item"]["address"])]
    # 誕生日
    birthday = user_info["Item"]["birthday"].replace("-", "/")
    # 性別
    if int(user_info["Item"]["sex"]) == 0:
      sex = "男性"
    elif int(user_info["Item"]["sex"]) == 1:
      sex = "女性"
    elif int(user_info["Item"]["sex"]) == 2:
      if genderless == 0:
        sex = "未選択(男性の場合)"
      else:
        sex = "未選択(女性の場合)"
      
    JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')
    today = datetime.datetime.now(JST).date()
    age = relativedelta(today, datetime.datetime.strptime(user_info["Item"]["birthday"], '%Y-%m-%d')).years
    
    url = result_one[1]
    
    if genderless == 0: # 1の場合は女性のデータを返す(ジェンダーレスの場合は0, 1で2度この関数を呼ぶ)
      result = result_one[0]
    else:
      result = result_one[2]
    available = [i for i, x in enumerate(result) if x == 0]  # 受診可能
    approaching_index = [i for i, x in enumerate(result) if x >= 1]
    approaching = [[i, result[i]] for i, x in enumerate(result) if x >= 1]  # 受診可能
    inavailable = [i for i, x in enumerate(result) if x == -1] # 未実施
    
    return {"address": address, "birthday": birthday, "sex": sex, "today": today.strftime('%Y/%m/%d'), "age": age, "url": url, "available": available, "inavailable": inavailable, "approaching": approaching}
    
    
def create_image(inform_data):
  # S3からテンプレート画像の読み込み
    image = image_function.download_file("templete.png") # Image.openされたデータを取得
    """
      画像に加筆する処理
    """
    # フォントデータをS3から取得
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket="ganjiinstant", Key="TTF File")
    font_data = io.BytesIO(response['Body'].read())
    
    
    # 今日の日付、年齢、性別、自治体の書き込み
    info_text = inform_data["today"] + "時点・" + str(inform_data["age"]) + "歳・" + inform_data["sex"]+ "・" + inform_data["address"] + "在住" # 日付・年齢・性別・居住地の情報
    print(info_text)
    font = ImageFont.truetype(font_data, 28)  # フォント・サイズの指定
    draw = ImageDraw.Draw(image)  # Drawオブジェクトを生成  
    draw.multiline_text((160, 135), info_text, fill=(100,100,100), font=font) # 文字の描画
    
    # 受診可能な検診の書き込み
    available_text = [cancer_list[x] for i , x in enumerate(inform_data["available"])]
    print("Available:", available_text)
    #font = ImageFont.truetype(font_data2, 48)  # フォント・サイズの指定
    for i, x in enumerate(available_text):
      if i<3:
        draw.multiline_text((220, 375+i*60), x, fill=(40,40,40), font=font) # 文字の描画
      else:
        draw.multiline_text((530, 375+(i-3)*60), x, fill=(40,40,40), font=font) # 文字の描画
    
    # 将来な検診の書き込み
    approaching_text = [[cancer_list[x[0]], x[1]] for i , x in enumerate(inform_data["approaching"])]
    print("Approaching:", approaching_text)
    for i, x in enumerate(approaching_text):
      if i<3:
        draw.multiline_text((220, 705+i*60), x[0]+"("+str(x[1])+"歳)", fill=(40,40,40), font=font) # 文字の描画
      else:
        draw.multiline_text((530, 705+(i-3)*60), x[0]+"("+str(x[1])+"歳)", fill=(40,40,40), font=font) # 文字の描画
    # S3にアップロード
    image_url = image_function.get_presigned_url(image)["Location"]
    print("instant url:", image_url)
    return image_url
    
# プッシュメッセージの送信
def push_message(user_id, messages):
  # POSTリクエストの準備(検診情報の送信)
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        'Authorization': 'Bearer ' + os.environ['ACCESSTOKEN']
    }
    data = {
        "to": user_id,
        "messages": messages
    }
    
    # POSTリクエスト
    req = urllib.request.Request(url=url, data=json.dumps(data).encode("utf-8"), method="POST", headers=headers)
    
    with urllib.request.urlopen(req) as res:
        
        logger.info(res.read().decode("utf-8"))
        
        return {
            "statusCode": 200,
            "body": json.dumps("Hello from Lambda!")
        }
  
        
# 検診情報の送信
def info_send(event):
    logger.info(json.dumps(event))
    
    # user IDの取り出し・検診情報の問い合わせ
    user_id = event["source"]["userId"]
    print("User ID:", user_id, ", Info_send")
    user_info = data_function.get_data(user_id)  # ユーザー情報
    result_one = data_function.ignite_one(user_id)  # 検診情報
      
    """
    登録情報が足りずに、検診情報がNoneだった場合
    """
    if result_one == None:
      # POSTリクエストの準備(返信)
      url = "https://api.line.me/v2/bot/message/reply"
      headers = {
          "Content-Type": "application/json",
          'Authorization': 'Bearer ' + os.environ['ACCESSTOKEN']
      }
      data = {
          "replyToken": event["replyToken"],
          "messages": [
              {
                "type": "text",
                "text": "登録を済ませるとご確認いただけます。",
              }
            ]
      }
      # POSTリクエスト
      req = urllib.request.Request(url=url, data=json.dumps(data).encode("utf-8"), method="POST", headers=headers)
      with urllib.request.urlopen(req) as res:
          
          logger.info(res.read().decode("utf-8"))
          
          return {
              "statusCode": 200,
              "body": json.dumps("Hello from Lambda!")
          }
      return None
      
    
    inform_data = data_extract(user_info, result_one)  # 書き込み用の情報に変換
    print(inform_data)
    if user_info["Item"]["sex"] == 2: # 性別未選択の場合
      inform_data2 = data_extract(user_info, result_one, genderless=1) # 女性の場合のデータも抽出する
    
    # POSTリクエストの準備(返信)
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        'Authorization': 'Bearer ' + os.environ['ACCESSTOKEN']
    }
    data = {
        "replyToken": event["replyToken"],
        "messages": [
            {
              "type": "text",
              "text": "がん検診を検索しています。少しお待ちください。",
            }
          ]
    }
    # POSTリクエスト
    req = urllib.request.Request(url=url, data=json.dumps(data).encode("utf-8"), method="POST", headers=headers)
    with urllib.request.urlopen(req) as res:
        logger.info(res.read().decode("utf-8"))
        
    # 画像の生成
    image_url = create_image(inform_data)
      
    """
    プッシュ送信の準備
    """
    if user_info["Item"]["sex"] != 2: # 性別選択の場合
      messages = [
        {
          "type": "text",
          "text": "自治体で受けられるがん検診をお知らせします。",
        },
        {
          "type": "image",
          "originalContentUrl": image_url,
          "previewImageUrl": image_url
        },
        {
          "type": "image",
          "originalContentUrl": grade_info_image,
          "previewImageUrl": grade_info_image
        },
        {
          "type":"flex",
          "altText": "予約方法・詳しい条件を確認する",
          "contents": 
              {
                "type": "bubble",
                "header": {
                  "type": "box",
                  "layout": "vertical",
                  "contents": [
                    {
                      "type": "text",
                      "text": "予約方法・詳しい条件を確認する",
                      "align": "center",
                      "weight": "bold"
                    }
                  ],
                  "backgroundColor": "#EEEEEE",
                  "height": "60px"
                },
                "body": {
                  "type": "box",
                  "layout": "vertical",
                  "contents": [
                    {
                      "type": "button",
                      "action": {
                        "type": "uri",
                        "label": "自治体ページへ",
                        "uri": inform_data["url"]
                      },
                      "style": "primary"
                    }
                  ]
                }
              }
        }
      ]
      
      # プッシュの送信
      push_message(user_id, messages)
    
    else:
      messages1 = [
          {
            "type": "text",
            "text": "自治体で受けられるがん検診をお知らせします。",
          },
          {
            "type": "image",
            "originalContentUrl": image_url,
            "previewImageUrl": image_url
          },
        ]
      push_message(user_id, messages1)
      
      image_url2 = create_image(inform_data2)
      messages2 = [
        {
          "type": "image",
          "originalContentUrl": image_url2,
          "previewImageUrl": image_url2
        },
        {
          "type": "image",
          "originalContentUrl": grade_info_image,
          "previewImageUrl": grade_info_image
        },
        {
          "type":"flex",
          "altText": "予約方法・詳しい条件を確認する",
          "contents": 
              {
                "type": "bubble",
                "header": {
                  "type": "box",
                  "layout": "vertical",
                  "contents": [
                    {
                      "type": "text",
                      "text": "予約方法・詳しい条件を確認する",
                      "align": "center",
                      "weight": "bold"
                    }
                  ],
                  "backgroundColor": "#EEEEEE",
                  "height": "60px"
                },
                "body": {
                  "type": "box",
                  "layout": "vertical",
                  "contents": [
                    {
                      "type": "button",
                      "action": {
                        "type": "uri",
                        "label": "自治体ページへ",
                        "uri": inform_data["url"]
                      },
                      "style": "primary"
                    }
                  ]
                }
              }
        }
      ]
      push_message(user_id, messages2)
        

    
    

# 自治体情報の保存・検診情報の送信
def city_save(event):
    """
       自治体データの格納の処理を描く
    """
    user_id = event["source"]["userId"]
    city = event["postback"]["data"].split(", ")[1]
    print("User ID:", user_id, ", City:", city)
    data_function.modify_data(user_id, address = int(city)) #自治体情報 #DBに送信
    
    """
    情報送信
    """
    user_info = data_function.get_data(user_id)  # ユーザー情報
    result_one = data_function.ignite_one(user_id)  # 検診情報
    inform_data = data_extract(user_info, result_one)  # 書き込み用の情報に変換
    print(inform_data)
    if user_info["Item"]["sex"] == 2: # 性別未選択の場合
      inform_data2 = data_extract(user_info, result_one, genderless=1) # 女性の場合のデータも抽出する
    
    """
    一旦返信
    """
    logger.info(json.dumps(event))
    # POSTリクエストの準備(返信)
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        'Authorization': 'Bearer ' + os.environ['ACCESSTOKEN']
    }
    data = {
        "replyToken": event["replyToken"],
        "messages": [
            {
                  "type": "text",
                  "text": "情報を登録しました。",
              },
            {
                  "type": "text",
                  "text": "がん検診を検索中です。少しお待ちください。",
              },
          ]
    }
    # POSTリクエスト
    req = urllib.request.Request(url=url, data=json.dumps(data).encode("utf-8"), method="POST", headers=headers)
    with urllib.request.urlopen(req) as res:
        logger.info(res.read().decode("utf-8"))
    
    # 画像の生成
    image_url = create_image(inform_data)  
    
    """
    プッシュ送信の準備
    """
    if user_info["Item"]["sex"] != 2: # 性別選択の場合
      messages = [
        {
          "type": "text",
          "text": "自治体で受けられるがん検診をお知らせします。",
        },
        {
          "type": "image",
          "originalContentUrl": image_url,
          "previewImageUrl": image_url
        },
        {
          "type": "image",
          "originalContentUrl": grade_info_image,
          "previewImageUrl": grade_info_image
        },
        {
          "type":"flex",
          "altText": "予約方法・詳しい条件を確認する",
          "contents": 
              {
                "type": "bubble",
                "header": {
                  "type": "box",
                  "layout": "vertical",
                  "contents": [
                    {
                      "type": "text",
                      "text": "予約方法・詳しい条件を確認する",
                      "align": "center",
                      "weight": "bold"
                    }
                  ],
                  "backgroundColor": "#EEEEEE",
                  "height": "60px"
                },
                "body": {
                  "type": "box",
                  "layout": "vertical",
                  "contents": [
                    {
                      "type": "button",
                      "action": {
                        "type": "uri",
                        "label": "自治体ページへ",
                        "uri": inform_data["url"]
                      },
                      "style": "primary"
                    }
                  ]
                }
              }
        }
      ]
      
      # プッシュの送信
      push_message(user_id, messages)
    
    else:
      messages1 = [
          {
            "type": "text",
            "text": "自治体で受けられるがん検診をお知らせします。",
          },
          {
            "type": "image",
            "originalContentUrl": image_url,
            "previewImageUrl": image_url
          },
        ]
      push_message(user_id, messages1)
      
      image_url2 = create_image(inform_data2)
      messages2 = [
        {
          "type": "image",
          "originalContentUrl": image_url2,
          "previewImageUrl": image_url2
        },
        {
          "type": "image",
          "originalContentUrl": grade_info_image,
          "previewImageUrl": grade_info_image
        },
        {
          "type":"flex",
          "altText": "予約方法・詳しい条件を確認する",
          "contents": 
              {
                "type": "bubble",
                "header": {
                  "type": "box",
                  "layout": "vertical",
                  "contents": [
                    {
                      "type": "text",
                      "text": "予約方法・詳しい条件を確認する",
                      "align": "center",
                      "weight": "bold"
                    }
                  ],
                  "backgroundColor": "#EEEEEE",
                  "height": "60px"
                },
                "body": {
                  "type": "box",
                  "layout": "vertical",
                  "contents": [
                    {
                      "type": "button",
                      "action": {
                        "type": "uri",
                        "label": "自治体ページへ",
                        "uri": inform_data["url"]
                      },
                      "style": "primary"
                    }
                  ]
                }
              }
        }
      ]
      push_message(user_id, messages2)

# アンフォロー時に情報を削除する      
def unfollow_process(event):
  user_id = event["source"]["userId"]
  print("User ID:", user_id)
  data_function.delete_data(user_id)
  
  # POSTリクエストの準備(送信) ※設定しているものの、ブロック中なので送れない。
  url = "https://api.line.me/v2/bot/message/push"
  headers = {
      "Content-Type": "application/json",
      'Authorization': 'Bearer ' + os.environ['ACCESSTOKEN']
  }
  data = {
      "to": user_id,
      "messages": [
          {
            "type": "text",
            "text": "登録情報を削除しました。",
          }
        ]
  }
  # POSTリクエスト
  req = urllib.request.Request(url=url, data=json.dumps(data).encode("utf-8"), method="POST", headers=headers)
  with urllib.request.urlopen(req) as res:
    
    logger.info(res.read().decode("utf-8"))
    
    return {
        "statusCode": 200,
        "body": json.dumps("Hello from Lambda!")
    }
    
    
# 定期実行の関数・開発中
def scheduled_ignite(event):
  result = data_function.ignite_all(birth_only=1)
  print("取得結果:", result)
  for user_id in result: # キーの取り出し
    # 以降、各ユーザーに対する送信処理を描く
    # user IDの取り出し・検診情報の問い合わせ
    print("User ID:", user_id, ", Scheduled_Info_send")
    user_info = data_function.get_data(user_id)  # ユーザー情報
    result_one = data_function.ignite_one(user_id)  # 検診情報

    
    inform_data = data_extract(user_info, result_one)  # 書き込み用の情報に変換
    print(inform_data)
    if user_info["Item"]["sex"] == 2: # 性別未選択の場合
      inform_data2 = data_extract(user_info, result_one, genderless=1) # 女性の場合のデータも抽出する
    
    # 画像の生成
    image_url = create_image(inform_data)
      
    """
    プッシュ送信の準備
    """
    if user_info["Item"]["sex"] != 2: # 性別選択の場合
      messages = [
        {
          "type": "text",
          "text": "こんにちは、自治体で受けられるがん検診のお知らせ日です。",
        },
        {
          "type": "image",
          "originalContentUrl": image_url,
          "previewImageUrl": image_url
        },
        {
          "type": "image",
          "originalContentUrl": grade_info_image,
          "previewImageUrl": grade_info_image
        },
        {
          "type":"flex",
          "altText": "予約方法・詳しい条件を確認する",
          "contents": 
              {
                "type": "bubble",
                "header": {
                  "type": "box",
                  "layout": "vertical",
                  "contents": [
                    {
                      "type": "text",
                      "text": "予約方法・詳しい条件を確認する",
                      "align": "center",
                      "weight": "bold"
                    }
                  ],
                  "backgroundColor": "#EEEEEE",
                  "height": "60px"
                },
                "body": {
                  "type": "box",
                  "layout": "vertical",
                  "contents": [
                    {
                      "type": "button",
                      "action": {
                        "type": "uri",
                        "label": "自治体ページへ",
                        "uri": inform_data["url"]
                      },
                      "style": "primary"
                    }
                  ]
                }
              }
        }
      ]
      
      # プッシュの送信
      push_message(user_id, messages)
    
    else:
      messages1 = [
          {
            "type": "text",
            "text": "自治体で受けられるがん検診をお知らせします。",
          },
          {
            "type": "image",
            "originalContentUrl": image_url,
            "previewImageUrl": image_url
          },
        ]
      push_message(user_id, messages1)
      
      image_url2 = create_image(inform_data2)
      messages2 = [
        {
          "type": "image",
          "originalContentUrl": image_url2,
          "previewImageUrl": image_url2
        },
        {
          "type": "image",
          "originalContentUrl": grade_info_image,
          "previewImageUrl": grade_info_image
        },
        {
          "type":"flex",
          "altText": "予約方法・詳しい条件を確認する",
          "contents": 
              {
                "type": "bubble",
                "header": {
                  "type": "box",
                  "layout": "vertical",
                  "contents": [
                    {
                      "type": "text",
                      "text": "予約方法・詳しい条件を確認する",
                      "align": "center",
                      "weight": "bold"
                    }
                  ],
                  "backgroundColor": "#EEEEEE",
                  "height": "60px"
                },
                "body": {
                  "type": "box",
                  "layout": "vertical",
                  "contents": [
                    {
                      "type": "button",
                      "action": {
                        "type": "uri",
                        "label": "自治体ページへ",
                        "uri": inform_data["url"]
                      },
                      "style": "primary"
                    }
                  ]
                }
              }
        }
      ]
      push_message(user_id, messages2)
  





"""
実行部分
"""
def lambda_handler(event, context):
    # EventBridgeからの呼び出しへの対応
    if "detail-type" in event and "account" in event:
      if event["account"] == "714296153216": # アカウント番号の確認
        # ignite_everyday呼び出しへの対応
        if "rule/ignite_everyday" in event["resources"][0]:
          print(event)
          # 重複呼び出しの防止
          if data_function.duplication_check() == 1:
            return 1
          else:
            print("---SCHEDULED EVENT START---")
            scheduled_ignite(event)
      return 0
  
    print("---REACTION START---")
    # アクションタイプの確認
    print(event)
    type = json.loads(event["body"])["events"][0]["type"] # message, follow,...
    print("type:", type)
    
   #各種関数の呼び出し
    # フォロー
    if type =="follow":
      for events in json.loads(event["body"])["events"]: # フォロー時
        print("フォロー時の処理")
        follow_message(events) 
            
    # アンフォロー
    elif type =="unfollow":
      for events in json.loads(event["body"])["events"]: # フォロー解除時
        print("フォロー解除時の処理")
        unfollow_process(events)
          
          
    # メッセージを受け取った場合
    elif type == "message": 
      for events in json.loads(event["body"])["events"]:
        
        if events["message"]["text"] == "登録情報の変更/削除": # リッチメニューから情報変更
          print("登録情報の変更・削除の呼び出し") #処理
          data_edit(events)
    
        elif events["message"]["text"] == "自治体のがん検診を見る": # リッチメニューから参照
          print("がん検診の通知の実行") #処理
          info_send(events)
        
    
        else: # その他
          print("本来は答えられないとメッセージを送る")
          send_sorry(events)
      
      
    # ポストバック時
    elif type =="postback": 
        for events in json.loads(event["body"])["events"]:
            data = events["postback"]["data"]
          
            if data=="birth":  # 誕生日情報のが帰ってきた時
              birth_save(events) # 誕生日情報の格納
              
            elif data.startswith("gender"):  # 性別選択の情報の場合
              if data.endswith("3"): # 性別不選択が選ばれた場合
                print("性別不選択の確認")
                genderless_ask(events)
              elif data.endswith(("0", "1", "2")): # 性別が確定できる場合(男・女もしくは不選択確認画面ではい)
                print("性別の登録")
                gender_save(events)
                
              
            elif data.startswith("area"): # 地域選択で地域が選ばれた場合
              print("自治体選択の送信")
              
            elif data.startswith("localgov"): # 自治体が選択された場合
              print("自治体の登録")
              city_save(events)
              
            elif data.startswith("select"):
              if data.endswith("gender"):
                reselect_gender(events)
                
              #elif data.endswith("area"):
               # print("地域選択の送信")
                
            elif data.startswith("data"):
              if data.endswith("delete"):
                print("データ削除について")
                delete_request(events)
                
              elif data.endswith("edit"):
                print("データ編集について")
                reregister(events)
              
              
            
          