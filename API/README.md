# API Reference

This file consolidates all available camera APIs into one reference with full endpoint URLs, request JSON bodies, and Postman-ready examples.

- Total API pages consolidated: `641`
- Top-level categories: `17`
- Base URL placeholder used below: `http://000.00.00.000`

## Read This First

- `Backend-verified` means the request body matches what your backend actually uses today.
- `Vendor-sourced` means the JSON was extracted from the imported camera documentation and may still need device-side validation.
- If a supposed request body starts with `"result": "success"`, it is probably a response-shaped sample, not a safe request payload to paste into Postman unchanged.
- If Postman returns `{"error_code":"expired"}`, your `X-csrftoken` or session cookie has expired. Log in again with `POST http://000.00.00.000/API/Web/Login`, then retry with a fresh token and cookie.

## Backend-Critical APIs

Your backend currently depends on these camera APIs:

- `POST http://000.00.00.000/API/Web/Login`
- `POST http://000.00.00.000/API/AI/processAlarm/Get`

For your app, use these request bodies exactly:

```json
{
  "data": {}
}
```

for login, and

```json
{}
```

for `processAlarm/Get`.

## How To Use With Postman

### Login and session setup

1. Create a `POST` request to `http://000.00.00.000/API/Web/Login`.
2. Use `Authorization -> Digest Auth` in Postman if the device expects digest authentication.
3. Add `Content-Type: application/json`.
4. Send the login JSON body shown in the `Login / Web / Login` section below.
5. Copy `X-csrftoken` from the response headers and keep the session cookie returned by the device.
6. Reuse both values on later protected API calls.

### Sending configuration or command data

1. Set Postman method to `POST`.
2. Use the exact endpoint listed for the API action.
3. Add headers such as `Content-Type: application/json`, `X-csrftoken`, and `Cookie` when required.
4. Paste the JSON request body shown under that action into `Body -> raw -> JSON`.
5. Click `Send`.

### Retrieving data

Many vendor read operations are named `Get`, `Range`, or `Search`, but they still use the HTTP `POST` method. In Postman, use the exact endpoint shown for that action and send the documented JSON body, even when the action name contains `Get`.

### Common headers template for protected APIs

```http
Content-Type: application/json
X-csrftoken: <token-from-login>
Cookie: session=<session-id>
```

### URL template

```http
POST http://000.00.00.000<endpoint>
```

## API Catalog

## AI

### Attribute_Detection

#### Attribute Detection

- Source page: `AI/Attribute_Detection/API.html`
- Purpose: This API is used to get or set AI > Attribute Detection page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Alarm/AttributeDetect/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Attribute_Detection/Get.html`
- Purpose: This API is used to get parameter for AI > Attribute Detection page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Alarm/AttributeDetect/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel": [
            "CH5"
        ]
    }
}
```

#### Range

- Source page: `AI/Attribute_Detection/Range.html`
- Purpose: This API is used to get parameter range for AI > Attribute Detection page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Alarm/AttributeDetect/Range
```
- Validation note: This vendor sample is response-shaped because it begins with `"result": "success"`. Treat it as a response example, not a confirmed request body.
- Request Body (JSON):
```json
{
    "result": "success",
    "data": {}
}
```

#### Set

- Source page: `AI/Attribute_Detection/Set.html`
- Purpose: This API is used to set parameter for AI > Attribute Detection page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Alarm/AttributeDetect/Set
```
- Validation note: The JSON below also looks response-shaped because it begins with `"result": "success"`. Do not assume it is a valid `Set` payload without confirming the expected fields from the device.
- Request Body (JSON):
```json
{
    "result": "success",
    "data": {
        "channel_info": {
            "CH1": {
                "alarm_type": "Close",
                "record_enable": false,
                "post_recording": "5",
                "send_email": false,
                "ftp_picture_upload": false,
                "picture_to_cloud": false,
                "http_listening": false,
                "schedule": [
                    {
                        "schedule_type": "SendEmail",
                        "week": [
                            {
                                "day": "Sun",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Mon",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Tue",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Wed",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Thu",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Fri",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Sat",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            }
                        ]
                    },
                    {
                        "schedule_type": "FtpPicUpload",
                        "week": [
                            {
                                "day": "Sun",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Mon",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Tue",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Wed",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Thu",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Fri",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Sat",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            }
                        ]
                    },
                    {
                        "schedule_type": "CloudPicUpload",
                        "week": [
                            {
                                "day": "Sun",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Mon",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Tue",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Wed",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Thu",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Fri",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Sat",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            }
                        ]
                    },
                    {
                        "schedule_type": "Record",
                        "week": [
                            {
                                "day": "Sun",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Mon",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Tue",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Wed",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Thu",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Fri",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            },
                            {
                                "day": "Sat",
                                "time": [
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
                                    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    }
}
```

### Cross_Counting_Scenario / Config

#### Config

- Source page: `AI/Cross_Counting_Scenario/Config/API.html`
- Purpose: This API is used for get or set AI > Cross Counting Scenario > Config parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Scenario/CC/Config/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Cross_Counting_Scenario/Config/Get.html`
- Purpose: This API is used to get AI > Cross Counting Scenario > Config configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Scenario/CC/Config/Get
```
- Request Body (JSON):
```json
{
    "result": "success",
    "data": {
        ["CH1"]
    }
}
```

#### Set

- Source page: `AI/Cross_Counting_Scenario/Config/Set.html`
- Purpose: This API is used to set AI > Cross Counting Scenario > Config configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Scenario/CC/Config/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "adSwitch": false,
        "ad_displayMode": false,
        "ad_seqTime": 1,
        "channel_info": {
            "CH1": {
                "channel_switch": false,
                "channel_group": -1,
                "channel_capacity": 11,
                "chn_set_enable": false,
                "chn_buzzer": "0",
                "chn_alarm_out": [],
                "chn_latch_time": "20"
            },
            "CH8": {
                "channel_switch": false,
                "channel_group": 4,
                "channel_capacity": 33,
                "chn_set_enable": false,
                "chn_buzzer": "0",
                "chn_alarm_out": [],
                "chn_latch_time": "10"
            }
        },
        "group_info": {
            "Group1": {
                "group_switch": false,
                "group_capacity": 30,
                "start_time": "00:00:00",
                "end_time": "23:59:59",
                "alarm_type": "Person",
                "grp_buzzer": "0",
                "grp_alarm_out": [],
                "grp_latch_time": "10"
            },
            "Group8": {
                "group_switch": false,
                "group_capacity": 10,
                "start_time": "00:00:00",
                "end_time": "23:59:29",
                "alarm_type": "Person",
                "grp_buzzer": "0",
                "grp_alarm_out": [],
                "grp_latch_time": "10"
            }
        }
    }
}
```

### Cross_Counting_Scenario / Image_Manage

#### Image Manage

- Source page: `AI/Cross_Counting_Scenario/Image_Manage/API.html`
- Purpose: This API is used for set AI > Cross Counting Scenario > Image Manage parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Scenario/CC/Config/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Set

- Source page: `AI/Cross_Counting_Scenario/Image_Manage/Set.html`
- Purpose: This API is used to set AI > Cross Counting Scenario > Image Manage configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Scenario/CC/Config/ImageManage
```
```http
POST http://000.00.00.000/API/AI/Scenario/CC/Config/ImageManage
```
```http
POST http://000.00.00.000/API/AI/Scenario/CC/Config/ImageManage
```
```http
POST http://000.00.00.000/API/AI/Scenario/CC/Config/ImageManage
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "operate": "GetImageList"
    }
}
```
```json
{
    "result": "success",
    "data": {
        "operate": "AddImage",
        "image_name": "eeeeee.jpg",
        "image_data": " base64(imgData)"
    }
}
```
```json
{
    "version": "1.0",
    "data": {
        "operate": "DeleteImage",
        "image_list": [
            "c278.png",
            "c236.png",
            "c263.png"
        ]
    }
}
```
```json
{
    "version": "1.0",
    "data": {
        "operate": "GetImageData",
        "image_name": "c70.png"
    }
}
```

### Cross_Counting_Scenario / Map

#### Map

- Source page: `AI/Cross_Counting_Scenario/Map/API.html`
- Purpose: This API is used for get or set AI > Cross Counting Scenario > Map parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Scenario/CC/MapConfig/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Cross_Counting_Scenario/Map/Get.html`
- Purpose: This API is used to get AI > Cross Counting Scenario > Map configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Scenario/CC/MapConfig/Get
```
- Request Body (JSON):
```json
{
    "data": {
        "GroupId": 0
    }
}
```

#### Set

- Source page: `AI/Cross_Counting_Scenario/Map/Set.html`
- Purpose: This API is used to set AI > Cross Counting Scenario > Map configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Scenario/CC/MapConfig/Set
```
- Request Body (JSON):
```json
{
    "data": {
        "GroupId": 0,
        "RefWidth": 1920,
        "RefHeight": 1080,
        "CamPos": [
            {
                "ChnId": 0,
                "XPos": 100,
                "YPos": 100
            },
            {
                "ChnId": 2,
                "XPos": 100,
                "YPos": 100
            }
        ],
		"MapImage": "base64"	//(选填)
    }
}
```

### Cross_Counting_Scenario / RealTime_Info

#### RealTime Info

- Source page: `AI/Cross_Counting_Scenario/RealTime_Info/API.html`
- Purpose: This API is used for get or set AI > Cross Counting Scenario > RealTime Info parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Scenario/CC/RealTime/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Cross_Counting_Scenario/RealTime_Info/Get.html`
- Purpose: This API is used to get AI > Cross Counting Scenario > RealTime Info configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Scenario/CC/RealTime/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "msgType": "get_CCScenario_RTData"
    }
}
```

#### Set

- Source page: `AI/Cross_Counting_Scenario/RealTime_Info/Set.html`
- Purpose: This API is used to set AI > Cross Counting Scenario > RealTime Info configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Scenario/CC/RealTime/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "msgType": "clear_CCScenario_RTData",
	    "clear_type": "Group",
        "groupId": 1
    }
}
```

### Cross_Counting_Scenario / Statistics

#### Statistics

- Source page: `AI/Cross_Counting_Scenario/Statistics/API.html`
- Purpose: This API is used for get or set AI > Cross Counting Scenario > Statistics parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Scenario/CC/Statistics/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Cross_Counting_Scenario/Statistics/Get.html`
- Purpose: This API is used to get AI > Cross Counting Scenario > Statistics configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Scenario/CC/Statistics/Get
```
- Request Body (JSON):
```json
{
    "result": "success",
    "data": {
        ["CH1"]
    }
}
```

#### Set

- Source page: `AI/Cross_Counting_Scenario/Statistics/Set.html`
- Purpose: This API is used to set AI > Cross Counting Scenario > Statistics configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Scenario/CC/Statistics/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "Channels": [
            0,
            3
        ],
        "Groups": [],
        "Date": "2021-01-14",
        "ReportType": "Week",
        "ChnObjType": [
            1,
            1
        ],
        "GrpObjType": []
    }
}
```

### Face Attendance(NVR dedicated)

#### Face Attendance

- Source page: `AI/Face Attendance(NVR dedicated)/API.html`
- Purpose: This API is used to get or set AI > Face Attendance(NVR专用) parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/FDAttendance/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Face Attendance(NVR dedicated)/Get.html`
- Purpose: This API is used to get parameter for Al > Face Attendance page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/FDAttendance/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `AI/Face Attendance(NVR dedicated)/Range.html`
- Purpose: This API is used to get parameter range for Al > Face Attendance page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/FDAttendance/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `AI/Face Attendance(NVR dedicated)/Set.html`
- Purpose: This API is used to set parameter for Al > Face Attendance page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/FDAttendance/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"fd_atd_info": {
        "enable": false,
        "mode": "Day",
        "mode_week": "Mon.",
        "mode_month_day": "1",
        "send_email": "08:30:00",
        "on_duty_time": "08:30:00",
        "off_duty_time": "17:30:00",
        "working_days": [
            "Mon.",
            "Tue.",
            "Wed.",
            "Thu.",
            "Fri."
        ],
        "group": [
            "1",
            "2",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
            "11",
            "12",
            "13",
            "14",
            "15",
            "16"
        ]
    }}
}
```

### Recongnition / Add Compare Face Image

#### Add

- Source page: `AI/Recongnition/Add Compare Face Image/Add.html`
- Purpose: This API is used to add AI > Recognition > Add Compare Face Image to compare faces.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/CompareFaces/Add
```
- Request Body (JSON):
```json
{
	"data": {
		"MsgId": null,
		"Count": 2,
		"WithImage": 0,	
		"WithFeature": 1	
		"FaceInfo": [
			{
				"Image1": "base64(imgData)",	
				"Feature": "base64(feature)",
				"FtVersion": 0	
			},
			{
				"Image1": "base64(imgData)",	
				"Feature": null,
				"FtVersion": 0	
			}
		]
	}
}
```

#### API

- Source page: `AI/Recongnition/Add Compare Face Image/API.html`
- Purpose: This API is used to add comparison faces
- Endpoint:
```http
POST http://000.00.00.000/API/AI/CompareFaces/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

### Recongnition / Additional Face Image

#### Add

- Source page: `AI/Recongnition/Additional Face Image/Add.html`
- Purpose: This API is used to add AI > Recognition > Additional Face Image face images.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/ExtraFaces/Add
```
- Request Body (JSON):
```json
{
	{
	"data": {
		"MsgId": null,
		"Count": 2,
		"ExtFaceInfo": [
			{
				"Id": -1,	
				"FaceId": 1,		
				"Image": "base64(imgData)",	
				"Feature": "base64(feature)",
				"FtVersion": 0		
			},
			{
				"Id": -1,	
				"FaceId": 1,		
				"Image": "base64(imgData)",	
				"Feature": "base64(feature)",
				"FtVersion": 0	
			}
		]
	}
}

}
```

#### API

- Source page: `AI/Recongnition/Additional Face Image/API.html`
- Purpose: This API is used to attach face images
- Endpoint:
```http
POST http://000.00.00.000/API/AI/ExtraFaces/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Recongnition/Additional Face Image/Get.html`
- Purpose: This API is used to get AI > Recognition > Additional Face Image face image parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/ExtraFaces/Get
```
- Request Body (JSON):
```json
{
	"data": {
		"MsgId": null,
		"FaceId": 1,
		"WithImage": 1,
		"WithFeature": 1
	}
}
```

#### GetById

- Source page: `AI/Recongnition/Additional Face Image/GetById.html`
- Purpose: This API is used to get AI > Recognition > Additional Face Image face image ID.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/ExtraFaces/GetById
```
- Request Body (JSON):
```json
{
	"data": {
		"MsgId": null,
		"FaceId": 1,
		"WithImage": 1,
		"WithFeature": 1
	}
}
```

#### Remove

- Source page: `AI/Recongnition/Additional Face Image/Remove.html`
- Purpose: This API is used to remove AI > Recognition > Additional Face Image face images.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/ExtraFaces/Remove
```
- Request Body (JSON):
```json
{
	"data": {
		"MsgId": null,
		"Count": 2,
		"ExtFaceInfo": [
			{
				"Id": 1,	
				"FaceId": 0,		
				"Image": null,	
				"Feature": null,
				"FtVersion": 0		
			},
			{
				"Id": 2,	
				"FaceId": 0,		
				"Image": null,	
				"Feature": null,
				"FtVersion": 0			
			}
		]
	}
}
```

### Recongnition / Database face information query

#### API

- Source page: `AI/Recongnition/Database face information query/API.html`
- Purpose: This API is used for AI > Recognition > Database face information query database face information query
- Endpoint:
```http
POST http://000.00.00.000/API/AI/AddedFaces/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### GetById

- Source page: `AI/Recongnition/Database face information query/GetById.html`
- Purpose: This API is used to get AI > Recognition > Database face information query face information.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/AddedFaces/GetById
```
- Request Body (JSON):
```json
{
	"data": {
		"MsgId": null,
		"FacesId": [1, 5, 6, 20, 53, 25], 
		"FacesMD5": ["F75C70ADB0B63B00E279E71B4143704D", 
					 "B74C70ADB0B63B00E279B71B4193704F", 
					 "A29B70ADB0B63B00E2793C1B4123504D",
					 "B34C70A3B0B53B00E279571B4143704F", 
					 "AC3C70ADB3B63B40E279EE1B41F3C04D",
					 "B74A70ADB0B63400E279E71B4143804F"],
					
		"SimpleInfo": 0 
		"WithImage": 1, 
		"WithFeature": 1, 
		"NeedMD5": 0 
	}
}
```

#### GetByIndex

- Source page: `AI/Recongnition/Database face information query/GetByIndex.html`
- Purpose: This API is used to get AI > Recognition > Database face information query face information.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/AddedFaces/GetByIndex
```
- Request Body (JSON):
```json
{
	"data":{
		"Msgid":null,
		"StartIndex":0,
		"count":16,
		"SimpleInfo":0,
		"WithImage":1,
		"WithFeature":1,
		"NeedMD5":0	
	}
}
```

#### GetId

- Source page: `AI/Recongnition/Database face information query/GetId.html`
- Purpose: This API is used to get added faces id.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/AddedFaces/GetId
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Search

- Source page: `AI/Recongnition/Database face information query/Search.html`
- Purpose: This API is used to search AI > Recognition > Database face information query face information.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/AddedFaces/Search
```
- Request Body (JSON):
```json
{
	"data": {
			"MsgId": null,
			"FaceInfo": [
				{
					"GrpId": 1,		
					"Time": 0,
					"Similarity": 0,
					"Sex": 0,		
					"Age": 0,
					"Chn": 0,
					"ModifyCnt": 0,	
					"Name": "",
					"Country": "",
					"Nation": "",
					"NativePlace": "",
					"IdCode": "",
					"Job": "",
					"Phone": "",
					"Email": "",
					"Domicile": "",
					"Remark": ""
				}
			]
		}
}
```

### Recongnition / Database license plate information query

#### Database license plate information query

- Source page: `AI/Recongnition/Database license plate information query/API.html`
- Purpose: This API is used to query  AI > Recognition > Database license plate information query the database license plate information
- Endpoint:
```http
POST http://000.00.00.000/API/AI/AddedPlates/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### GetById

- Source page: `AI/Recongnition/Database license plate information query/GetById.html`
- Purpose: This API is used to obtain license plate information by license plate id.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/AddedPlates/GetById
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### GetCount

- Source page: `AI/Recongnition/Database license plate information query/GetCount.html`
- Purpose: This API is used to get added license plates count.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/AddedPlates/GetCount
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### GetId

- Source page: `AI/Recongnition/Database license plate information query/GetId.html`
- Purpose: This API is used to get license plate id.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/AddedPlates/GetId
```
- Request Body (JSON):
```json
{
    "version":"1.0",
	"data": {
        "PlateInfo": [
            {   
                "Id": "粤CW"
            }
        ]
	}
}
```
```json
{
    "version":"1.0",
	"data": {
        "GrpId": [1, 2, 6]
	}
}
```

### Recongnition / Face Group

#### Add

- Source page: `AI/Recongnition/Face Group/Add.html`
- Purpose: This API is used to add AI > Recognition > FDGroup page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/FDGroup/Add
```
- Request Body (JSON):
```json
{
	"data": {
		"MsgId": null,					
		"Group": [
			{
				"DetectType": 0
			}
		]
	}
}
```

#### API

- Source page: `AI/Recongnition/Face Group/API.html`
- Purpose: This API is used to manipulate the Face Group parameter
- Endpoint:
```http
POST http://000.00.00.000/API/AI/FDGroup/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Change

- Source page: `AI/Recongnition/Face Group/Change.html`
- Purpose: This API is used to change the group to which a face belongs AI > Recognition > Face Group
- Endpoint:
```http
POST http://000.00.00.000/API/AI/FDGroup/Change
```
- Request Body (JSON):
```json
{
	"data": {
		"MsgId": null,
		"Count": 2,
		"Group": 1,
		"FaceInfo": [{
				"id": -1,
				"MD5":"F74C70ADB0B63B00E279E71B4143704D"
		}]
	}
}
```

#### Get

- Source page: `AI/Recongnition/Face Group/Get.html`
- Purpose: This API is used to get AI > Recognition > FDGroup page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/FDGroup/Get
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### GetId

- Source page: `AI/Recongnition/Face Group/GetId.html`
- Purpose: This API is used to get the AI > Recognition > FDGroup id.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/FDGroup/GetId
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "MsgId": "",
        "DefaultVal": 0,
        "SimpleInfo": 0,
        "TypeFlags": 1,
        "WithInternal": 0
    }
}
```

#### Modify

- Source page: `AI/Recongnition/Face Group/Modify.html`
- Purpose: This API is used to modify the AI > Recognition > FDGroup parameter.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Faces/Modify
```
- Request Body (JSON):
```json
{
	"data": {
		"MsgId": null,
		"Result": 0,
		"Count": 5,	
		"Group": [	
			{
				"Id": 2,
				"Name": "Block List",
				"DetectType": 0,
				"Policy": 0,
				"Enabled": 1,
				"CanDel": 0,
				"Similarity": 70,
				"PolicyConfigs": [
					{
						"ChnAlarmOut": [			
							[ [255, 255, 0, 255], [255, 255, 0, 255], [255, 255, 0, 255] ],
							[ [255, 255, 0, 255], [255, 255, 0, 255], [255, 255, 0, 255] ],
							...
							[ [255, 255, 0, 255], [255, 255, 0, 255], [255, 255, 0, 255] ]
						  ],
						  "ChnBuzzerOpt": [0, 1, 1, 2, 3, 4, 0, 1, 1, 3, 2, 2 ],
						  "LatchTimeOpt": [0, 1, 1, 2, 3, 4, 0, 1, 1, 3, 2, 2 ],
						  "SaveImg": [255, 255, 255, 255],
						  "SendEmail": [0, 0, 0, 0],
						  "UploadToFtp": [255, 255, 255, 255],
						  "UploadToCloud": [0, 0, 0, 0],
						  "ShowThumbnail": [255, 255, 255, 255],
						  "Record": [255, 255, 255, 255],
						  "Push": [0, 0, 0, 0],
						  "AlarmSchedule": [
							[				
								[255, 255, 255, 255, 255, 255],		
								...
							],
							[			
								[255, 255, 255, 255, 255, 255],
								...
							],
							...	
						]
					},
					{
						"ChnAlarmOut": [			
							[ [255, 255, 0, 255], [255, 255, 0, 255], [255, 255, 0, 255] ],	
							[ [255, 255, 0, 255], [255, 255, 0, 255], [255, 255, 0, 255] ],
							[ [255, 255, 0, 255], [255, 255, 0, 255], [255, 255, 0, 255] ],
							...
							[ [255, 255, 0, 255], [255, 255, 0, 255], [255, 255, 0, 255] ]
						  ],
						  "ChnBuzzerOpt": [0, 1, 1, 2, 3, 4, 0, 1, 1, 3, 2, 2 ],
						  "LatchTimeOpt": [0, 1, 1, 2, 3, 4, 0, 1, 1, 3, 2, 2 ],
						  "SaveImg": [255, 255, 255, 255],
						  "SendEmail": [0, 0, 0, 0],
						  "UploadToFtp": [255, 255, 255, 255],
						  "UploadToCloud": [0, 0, 0, 0],
						  "ShowThumbnail": [255, 255, 255, 255],
						  "Record": [255, 255, 255, 255],
						  "Push": [0, 0, 0, 0],
						  "AlarmSchedule": [
							[				
								[255, 255, 255, 255, 255, 255],		
								...
							],
							[				
								[255, 255, 255, 255, 255, 255],
								...
							],
							...				
						]
					}
				],
				"EnableChnAlarm": [255, 255, 255, 255]，
				"AlarmOut": {
					"Local": ["Local->1"],
					"Ipc": [{
						"Channel": 1,
						"AlarmOutCnt": 1
					}, {
						"Channel": 4,
						"AlarmOutCnt": 1
					}, {
						"Channel": 5,
						"AlarmOutCnt": 1
					}]
				}		
			},
			...	

		]
	}
}
```

#### Remove

- Source page: `AI/Recongnition/Face Group/Remove.html`
- Purpose: This API is used to remove AI > Recognition > FDGroup face groups.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/FDGroup/Remove
```
- Request Body (JSON):
```json
{
	"data": {
		"MsgId": null,					
		"Group": [
			{
				"Id": 4,
			}
		]
	}
}
```

### Recongnition / Face

#### Add

- Source page: `AI/Recongnition/Face/Add.html`
- Purpose: This API is used to add AI > Recognition > Faces faces.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Faces/Add
```
- Request Body (JSON):
```json
{
	"data": {
		"MsgId": null,
		"Count": 2,
		"FaceInfo": [
			{
				"Id": -1,		
				"GrpId": 1,		
				"Time": 0,
				"Similarity": 0,
				"Sex": 0,		
				"Age": 26,
				"Chn": 0,
				"ModifyCnt": 0,			
				"Image1": "base64(imgData)",		
				"Image2": null,			
				"Image3": null,			
				"Feature": "base64(feature)",
				"FtVersion": 0,	
				"Name": "Mike",
				"Country": "China",
				"Nation": "Han",
				"NativePlace": "Guangdong,Zhuhai",
				"IdCode": "415025199203050916",
				"Job": "Software",
				"Phone": "12345678902",
				"Email": "abcd@163.com",
				"Domicile": "Guangdong,Zhuhai,Xiangzhou ...",
				"Remark": "Detail of this person ...",
				"EnableChnAlarm": [255, 255, 255, 255] 
			}
		]
	}
}
```

#### API

- Source page: `AI/Recongnition/Face/API.html`
- Purpose: This API is used for parameter manipulation of faces
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Faces/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### GetImagesFeature

- Source page: `AI/Recongnition/Face/GetImagesFeature.html`
- Purpose: This API is used to get image feature values. AI > Recognition > Faces
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Faces/Modify
```
- Request Body (JSON):
```json
{
    "data": {
        "Images": "base64(imgData)"
    }
}
```

#### Modify

- Source page: `AI/Recongnition/Face/Modify.html`
- Purpose: This API is used to modify the AI > Recognition > Faces parameter.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Faces/Modify
```
- Request Body (JSON):
```json
{
	"data": {
		"MsgId": null,
		"Count": 2,
		"FaceInfo": [
			{
				"Id": -1,		
				"GrpId": 1,		
				"Time": 0,
				"Similarity": 0,
				"Sex": 0,		
				"Age": 26,
				"Chn": 0,
				"ModifyCnt": 0,			
				"Image1": "base64(imgData)",		
				"Image2": null,			
				"Image3": null,			
				"Feature": "base64(feature)",
				"FtVersion": 0	
				"Name": "Mike",
				"Country": "China",
				"Nation": "Han",
				"NativePlace": "Guangdong,Zhuhai",
				"IdCode": "415025199203050916",
				"Job": "Software",
				"Phone": "12345678902",
				"Email": "abcd@163.com",
				"Domicile": "Guangdong,Zhuhai,Xiangzhou ...",
				"Remark": "Detail of this person ...",
				"EnableChnAlarm": [255, 255, 255, 255] 
			}
		]
	}
}
```

#### Remove

- Source page: `AI/Recongnition/Face/Remove.html`
- Purpose: This API is used to remove the AI > Recognition > Faces parameter.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Faces/Remove
```
- Request Body (JSON):
```json
{
	"data": {
		"MsgId": null,
		"Count": 2,
		"FaceInfo": [
			{
				"Id": 2, 
				"MD5": "F74C70ADB0B63B00E279E71B4143704D"
			},
			{
				"Id": 3,
				"MD5": "0194F781438F2DE8FBE5B0469895036D"
			}
		]
	}
}
```

### Recongnition / License Plate Group

#### Add

- Source page: `AI/Recongnition/License Plate Group/Add.html`
- Purpose: This API is used to add a AI > Recognition > PlateGroup license plate group.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/PlateGroup/Add
```
- Request Body (JSON):
```json
{
	"data": {
        "Group": [	
			{
                "Name": "Test Group 1"
            },
            {
                "Name": "Test Group 2"
            }
       ]
	}
}
```

#### API

- Source page: `AI/Recongnition/License Plate Group/API.html`
- Purpose: This API is used for the operation of license plate groups
- Endpoint:
```http
POST http://000.00.00.000/API/AI/PlateGroup/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Recongnition/License Plate Group/Get.html`
- Purpose: This API is used to get the AI > Recognition > PlateGroup license plate group.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/PlateGroup/Get
```
- Request Body (JSON):
```json
{
	"data": {
		"MsgId": "",
		"DefaultVal": 0,
		"SimpleInfo": 1,
"GroupsId": [
            1,
            2,
            3，
			…
        ]
	}
}
```

#### GetId

- Source page: `AI/Recongnition/License Plate Group/GetId.html`
- Purpose: This API is used to get the AI > Recognition > PlateGroup license plate group id.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/PlateGroup/GetId
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "MsgId": "",
        "DefaultVal": 0,
        "SimpleInfo": 0,
        "TypeFlags": 1,
        "WithInternal": 0
    }
}
```

#### Modify

- Source page: `AI/Recongnition/License Plate Group/Modify.html`
- Purpose: This API is used to modify the AI > Recognition > PlateGroup license plate group.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Faces/Modify
```
- Request Body (JSON):
```json
{
    "data": {
        "Group": [
            {
                "Id": 7,
                "Name": "测试组1",
                "Policy": 0,
                "DetectType": 2,
                "Similarity": 1,
                "CanDel": 1,
                "Enabled": 1,
                "EnableAlarm": 1,
				"PolicyConfigs": [...],
				"EnableChnAlarm": [...],
				"AlarmOut": {...}
            },
			{
                "Id": 8,
                "Name": "测试组2",
                "Policy": 0,
                "DetectType": 2,
                "Similarity": 1,
                "CanDel": 1,
                "Enabled": 1,
                "EnableAlarm": 1,
				"PolicyConfigs": [...],
				"EnableChnAlarm": [...],
				"AlarmOut": {...}
            }
		]
	}
}
```

#### Remove

- Source page: `AI/Recongnition/License Plate Group/Remove.html`
- Purpose: This API is used to remove the AI > Recognition > PlateGroup license plate group.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/PlateGroup/Remove
```
- Request Body (JSON):
```json
{
	"data": {
        "Group": [
            {
                "Id": 7
            },
            {
                "Id": 8
            }
        ]
	}
}
```

### Recongnition / License Plate

#### Add

- Source page: `AI/Recongnition/License Plate/Add.html`
- Purpose: This API is used to add license plate.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Plates/Add
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### License Plate

- Source page: `AI/Recongnition/License Plate/API.html`
- Purpose: This API is used to add, delete, modify license plate and change the group to which the license plate belongs.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Plates/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Change

- Source page: `AI/Recongnition/License Plate/Change.html`
- Purpose: This API is used to change the group to which the license plate belongs.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Plates/ChangeGroup
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Modify

- Source page: `AI/Recongnition/License Plate/Modify.html`
- Purpose: This API is used to modify the license plate.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Plates/Modify
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data": {
        "PlateInfo": [
            {
                "Id": "粤CW2763",
                "GrpId": 6,
                "PlateColor": 1,
                "Sex": 1,
                "CarBrand": "大众",
                "CarType": "两厢车",
                "Owner": "张三三",
                "IdCode": "12125180",
                "Job": "职业",
                "Phone": "15271859302",
                "Domicile": "居住地1",
                "Remark": "备注",
                "EnableChnAlarm": []
            },
            {
                "Id": "粤CK3961",
                "GrpId": 6,
                "PlateColor": 2,
                "Sex": 1,
                "CarBrand": "大众",
                "CarType": "三厢车",
                "Owner": "李四四",
                "IdCode": "12125181",
                "Job": "职业",
                "Phone": "15271859303",
                "Domicile": "居住地2",
                "Remark": "备注",
                "EnableChnAlarm": []
            }
		]
    }
}
```

#### Remove

- Source page: `AI/Recongnition/License Plate/Remove.html`
- Purpose: This API is used to remove license plate.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Plates/Remove
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data": {
        "PlateInfo": [
            {
                "Id": "粤CW2763"
            },
            {
                "Id": "粤CK3961"
            }
		]
    }
}
```

### Recongnition / Model Configuratuon

#### API

- Source page: `AI/Recongnition/Model Configuratuon/API.html`
- Purpose: This API is used to get or set face model configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Model/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Recongnition/Model Configuratuon/Get.html`
- Purpose: This API is used to get AI > Recognition > Model Configuratuon page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Model/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
}
```

#### Set

- Source page: `AI/Recongnition/Model Configuratuon/Set.html`
- Purpose: This API is used to set AI > Recognition > Model Configuratuon  page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Model/Set
```
- Request Body (JSON):
```json
{
   {
    "result": "success",
    "data": {
        "rows": [
			{
                "channel": "local",
                "face_recognition": "------",
                "face_detection": "------",
                "enable_face_recognition": false
            },
            {
                "channel": "CH1",
                "face_recognition": "V0.2.0.0.1-release",
                "face_detection": "V0.2.1.2.1-release",
                "enable_face_recognition": true
            }
        ]
    }
}
}
```

### Recongnition / Snaped Faces and Objects Count Get (VHD)

#### Snaped Faces and Objects Count Get (VHD)

- Source page: `AI/Recongnition/Snaped Faces and Objects Count Get (VHD)/API.html`
- Purpose: This API is used to get VHD log count.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/VhdLogCount/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Recongnition/Snaped Faces and Objects Count Get (VHD)/Get.html`
- Purpose: This API is used to get VHD log count.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/VhdLogCount/Get
```
- Request Body (JSON): No JSON request body sample was documented on this page.

### Recongnition / Snaped Faces Search and Match

#### API

- Source page: `AI/Recongnition/Snaped Faces Search and Match/API.html`
- Purpose: This API is used for face search and matching of snapshots
- Endpoint:
```http
POST http://000.00.00.000/API/AI/SnapedFaces/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### GetById

- Source page: `AI/Recongnition/Snaped Faces Search and Match/GetById.html`
- Purpose: This API is used to match AI > Recognition > SnapedFaces snapshot face information ID.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/SnapedFaces/GetById
```
- Request Body (JSON):
```json
{
	"data": {
		"MsgId": null,
		"Result": 0, 
		"TotalCount": 600,  
		"Count": 20,	
		"SnapedFaceInfo": [
			{
				"UUId": 103,			
				"MatchedFaceId": 5,		
				"MatchedMD5": "294C703DB05F3B00E279E71B41437E46",  
				"Chn": 3,
				"StrChn":"4",
				"Similarity": 89.39759,	
				"StartTime": 1540444116, 
				"EndTime": 1540444136, 
				"FaceImage": "base64(imgData)",	
				"BodyImage": "base64(imgData)",	
				"Background": "base64(imgData)",	
				"Feature": "base64(feature)",
				"FtVersion": 0	
				"SnapId": 2375,
				"Type": 0, 
				"Score": 60,
				"Gender": 0, 
				"fAttrAge": 25, 
				"Beauty": 51，
				"GlassesType": 1, 
				"Expression": 0, 
				"MouthMask": 1,
				"Race": 1
			},
			{
				"UUId": 126,			
				"MatchedFaceId": 2,		
				"MatchedMD5": "F74C70ADB0B63B00E279E71B4143704D", 
				"Chn": 3,
				"StrChn":"4",
				"Similarity": 96.87693, 
				"StartTime": 1540444116, 
				"EndTime": 1540444136, 
				"FaceImage": "base64(imgData)",	
				"BodyImage": "base64(imgData)",	
				"Background": "base64(imgData)",	
				"Feature": "base64(feature)",
				"FtVersion": 0	
				"SnapId": 2376,
				"Type": 0, 
				"Score": 60,
				"Gender": 0, 
				"fAttrAge": 25, 
				"Beauty": 51，
				"GlassesType": 1, 
				"Expression": 0, 
				"MouthMask": 1,
				"Race": 1
			},
			{
				...
			},
			...
		]
	}
}
```

#### GetByIndex

- Source page: `AI/Recongnition/Snaped Faces Search and Match/GetByIndex.html`
- Purpose: This API is used to match AI > Recognition > SnapedFaces snapshot face information.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/SnapedFaces/GetByIndex
```
- Request Body (JSON):
```json
{
	"data": {
		"MsgId": null,
		"Engine": 0,		
		"MatchedFaces": 1,	
		"StartIndex": 0,
		"Count": 20,		
		"SimpleInfo": 1	,				
		"WithFaceImage": 1,	
		"WithBodyImage": 0, 
		"WithBackgroud": 0,	
		"WithFeature": 1	
	}
}
```

#### Search

- Source page: `AI/Recongnition/Snaped Faces Search and Match/Search.html`
- Purpose: This API is used to search AI > Recognition > SnapedFaces snapshot face information.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/SnapedFaces/Search
```
- Request Body (JSON):
```json
{
	"msgType": "AI_searchSnapedFaces",
	"data": {
		"MsgId": null,
		"StartTime": "2018-10-20 00:00:00",
		"EndTime": "2018-10-28 23:59:59",
		"Chn": [0, 1, 2, 3, 4, 5, 6, 7, 8],  
		"AlarmGroup": [1, 2, 5, 9, 13],   
		"Similarity": 70,	
		"Engine": 0,	
		"Count": 2,
		"FaceInfo": [
			{
				"Id": 2,
				"MD5": "F74C70ADB0B63B00E279E71B4143704D",
				"Feature": "base64(feature)",
				"FtVersion": 0	
			},
			{
				"Id": 5,	
				"MD5": "294C703DB05F3B00E279E71B41437E46",
				"Feature": "base64(feature)",
				"FtVersion": 0	
			}
		]
	}
}
```

#### StopSearch

- Source page: `AI/Recongnition/Snaped Faces Search and Match/StopSearch.html`
- Purpose: This API is used to stop searching for AI > Recognition > SnapedFaces snapshot face information.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/SnapedFaces/StopSearch
```
- Request Body (JSON):
```json
{
    "data": {
        "MsgId": null,
        "Engine": 0,
        "Result": -9
    }
}
```

### Recongnition / Snaped License Plates Search and Match

#### Snaped License Plates Search and Match

- Source page: `AI/Recongnition/Snaped License Plates Search and Match/API.html`
- Purpose: This API is used to  search and match license plates.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/SnapedObjects/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### SearchPlate

- Source page: `AI/Recongnition/Snaped License Plates Search and Match/SearchPlate.html`
- Purpose: This API is used to search and match license plates.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/SnapedObjects/SearchPlate
```
- Request Body (JSON): No JSON request body sample was documented on this page.

### Recongnition / Snaped Objects Search

#### API

- Source page: `AI/Recongnition/Snaped Objects Search/API.html`
- Purpose: This API is used for snapshot object search
- Endpoint:
```http
POST http://000.00.00.000/API/AI/SnapedObjects/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### GetById

- Source page: `AI/Recongnition/Snaped Objects Search/GetById.html`
- Purpose: This API is used to match AI > Recognition > SnapedObjects snapshot objects.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/SnapedObjects/GetById
```
- Request Body (JSON):
```json
{
	"data": {
		"MsgId": null,
		"Engine": 0,		
		"StartIndex": 0,	
		"Count": 20,		
		"SimpleInfo": 1，	
		"WithObjectImage": 0, 
		"WithBackgroud": 0 
	}
}
```

#### GetByIndex

- Source page: `AI/Recongnition/Snaped Objects Search/GetByIndex.html`
- Purpose: This API is used to match AI > Recognition > SnapedObjects snapshot object ID.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/SnapedObjects/GetByIndex
```
- Request Body (JSON):
```json
{
	"data": {
		"MsgId": null,
		"Engine": 0,		
		"StartIndex": 0,	
		"Count": 20,		
		"SimpleInfo": 1，	
		"WithObjectImage": 0, 
		"WithBackgroud": 0 
	}
}
```

#### Search

- Source page: `AI/Recongnition/Snaped Objects Search/Search.html`
- Purpose: This API is used to search for AI > Recognition > SnapedObjects snapshot objects.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/SnapedObjects/Search
```
- Request Body (JSON):
```json
{
	"data": {
		"MsgId": null,
		"StartTime": "2018-10-20 00:00:00",
		"EndTime": "2018-10-28 23:59:59",
		"Chn": [0, 1, 2, 3, 4, 5, 6, 7, 8],  
		"Type": [1, 2],       				
		"Engine": 0,
	}
}
```

#### StopSearch

- Source page: `AI/Recongnition/Snaped Objects Search/StopSearch.html`
- Purpose: This API is used to stop searching for AI > Recognition > SnapedObjects snapshot objects.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/SnapedObjects/StopSearch
```
- Request Body (JSON):
```json
{
    "data": {
        "MsgId": null,
        "Engine": 0,
        "Result": -9
    }
}
```

### Repeat_Customer

#### Repeat Customer

- Source page: `AI/Repeat_Customer/API.html`
- Purpose: This API is used to get AI > Repeat Customer:SnapedFeaturesId、AI > Repeat Customer:FilterSnapedFaces、AI > Repeat Customer:MatchAddedFaces parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Repeat_Customer/FGet.html`
- Purpose: It is used to get the AI > Repeat Customer:FilterSnapedFaces parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/FilterSnapedFaces/Get
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"MsgId": "",
		"Engine": 0,
		"MinInterval": 0,
		"Similarity": 70,
		"Filter": {
			"UUId": 20402,
			"FtId": 20402
		},
		"FtIdSet": {
			"UUIds": [20402, 20403, 20408, 20404, 20405, ...],
			"FtIds": [20402, 20403, 20408, 20404, 20405, ...]
		}
	}
}
```

#### Get

- Source page: `AI/Repeat_Customer/MGet.html`
- Purpose: It is used to get the AI > Repeat Customer:MatchAddedFaces parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/MatchAddedFaces/Get
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"MsgId": "",
		"Similarity": 70,
		"GrpIds": [],
		"Engine": 1,
		"UUIds": [21411, 21409, 21408, 21407, 21405, ...]
	}
}
```

#### Get

- Source page: `AI/Repeat_Customer/SGet.html`
- Purpose: It is used to get the AI > Repeat Customer:SnapedFeaturesId parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/SnapedFeaturesId/Get
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"MsgId": "",
		"StartIndex": 0,
		"Engine": 1,
		"Count": 1011
	}
}
```

### Setup / AI_Func_Schedule

#### AI Func Schedule

- Source page: `AI/Setup/AI_Func_Schedule/API.html`
- Purpose: This API is used for get or set AI > Setup > AI Func Schedule page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/AISchedule/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Setup/AI_Func_Schedule/Get.html`
- Purpose: This API is used to get parameter for AI > Setup > AI Func Schedule page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/AISchedule/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `AI/Setup/AI_Func_Schedule/Range.html`
- Purpose: This API is used to get parameter range for AI > Setup > AI Func Schedule page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/AISchedule/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `AI/Setup/AI_Func_Schedule/Set.html`
- Purpose: This API is used to set parameter for AI > Setup > AI Func Schedule page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/AISchedule/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"channel_info": {"CH1": {
        "AI_Schedule": false,
        "category": [
            {
                "schedule_type": "fd",
                "mutex_type": [
                    "pid",
                    "lcd",
                    "sod",
                    "pvd",
                    "cc",
                    "cd",
                    "qd",
                    "lpd"
                ],
                "week": [
                    {
                        "day": "Sun",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Mon",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Tue",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Wed",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Thu",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Fri",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Sat",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    }
                ]
            },
            {
                "schedule_type": "pvd",
                "mutex_type": [
                    "pid",
                    "lcd",
                    "sod",
                    "fd",
                    "cc",
                    "cd",
                    "qd",
                    "lpd"
                ],
                "week": [
                    {
                        "day": "Sun",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Mon",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Tue",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Wed",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Thu",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Fri",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Sat",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    }
                ]
            },
            {
                "schedule_type": "pid",
                "mutex_type": [
                    "sod",
                    "pvd",
                    "fd",
                    "cc",
                    "cd",
                    "qd",
                    "lpd"
                ],
                "week": [
                    {
                        "day": "Sun",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Mon",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Tue",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Wed",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Thu",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Fri",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Sat",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    }
                ]
            },
            {
                "schedule_type": "lcd",
                "mutex_type": [
                    "sod",
                    "pvd",
                    "fd",
                    "cc",
                    "cd",
                    "qd",
                    "lpd"
                ],
                "week": [
                    {
                        "day": "Sun",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Mon",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Tue",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Wed",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Thu",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Fri",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Sat",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    }
                ]
            },
            {
                "schedule_type": "sod",
                "mutex_type": [
                    "pid",
                    "lcd",
                    "pvd",
                    "fd",
                    "cc",
                    "cd",
                    "qd",
                    "lpd"
                ],
                "week": [
                    {
                        "day": "Sun",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Mon",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Tue",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Wed",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Thu",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Fri",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Sat",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    }
                ]
            },
            {
                "schedule_type": "cc",
                "mutex_type": [
                    "pid",
                    "lcd",
                    "sod",
                    "pvd",
                    "fd",
                    "cd",
                    "qd",
                    "lpd"
                ],
                "week": [
                    {
                        "day": "Sun",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Mon",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Tue",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Wed",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Thu",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Fri",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Sat",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    }
                ]
            },
            {
                "schedule_type": "cd",
                "mutex_type": [
                    "pid",
                    "lcd",
                    "sod",
                    "pvd",
                    "fd",
                    "cc",
                    "qd",
                    "lpd"
                ],
                "week": [
                    {
                        "day": "Sun",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Mon",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Tue",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Wed",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Thu",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Fri",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Sat",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    }
                ]
            },
            {
                "schedule_type": "qd",
                "mutex_type": [
                    "pid",
                    "lcd",
                    "sod",
                    "pvd",
                    "fd",
                    "cc",
                    "cd",
                    "lpd"
                ],
                "week": [
                    {
                        "day": "Sun",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Mon",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Tue",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Wed",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Thu",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Fri",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Sat",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    }
                ]
            },
            {
                "schedule_type": "lpd",
                "mutex_type": [
                    "pid",
                    "lcd",
                    "sod",
                    "pvd",
                    "fd",
                    "cc",
                    "cd",
                    "qd"
                ],
                "week": [
                    {
                        "day": "Sun",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Mon",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Tue",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Wed",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Thu",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Fri",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Sat",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    }
                ]
            },
            {
                "schedule_type": "hm",
                "mutex_type": [],
                "week": [
                    {
                        "day": "Sun",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Mon",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Tue",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Wed",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Thu",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Fri",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Sat",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    }
                ]
            },
            {
                "schedule_type": "rsd",
                "mutex_type": [],
                "week": [
                    {
                        "day": "Sun",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Mon",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Tue",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Wed",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Thu",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Fri",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    },
                    {
                        "day": "Sat",
                        "time": [
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
                            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
                        ]
                    }
                ]
            }
        ]
    }}}
}
```

### Setup / Cross Counting

#### Cross Counting

- Source page: `AI/Setup/Cross Counting/API.html`
- Purpose: This API is used to get or set Cross Counting configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/CrossCount/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Setup/Cross Counting/Get.html`
- Purpose: This API is used to get parameter for AI > Setup > Cross Counting page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/CrossCount/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "ChannelConfig"}
}
```

#### Range

- Source page: `AI/Setup/Cross Counting/Range.html`
- Purpose: This API is used to get parameter range for AI > Setup > Cross Counting page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/CrossCount/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "ChannelConfig"}
}
```

#### Set

- Source page: `AI/Setup/Cross Counting/Set.html`
- Purpose: This API is used to set parameter for AI > Setup > Cross Counting page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/CrossCount/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {"CH1": {
            "status": "Online",
            "switch": false,
            "sensitivity": 2,
            "alarm_num": 1,
            "type": "Pedestrian",
            "reset_count": false,
            "start_time": "00:00:00",
            "end_time": "23:59:59",
            "rule_info": {"rule_number1": {
                "rule_type": "A->B",
                "rule_switch": false,
                "rule_line": {
                    "x1": 0,
                    "y1": 0,
                    "x2": 0,
                    "y2": 0
                },
                "rule_rect": {
                    "x1": 0,
                    "y1": 0,
                    "x2": 0,
                    "y2": 0,
                    "x3": 0,
                    "y3": 0,
                    "x4": 0,
                    "y4": 0
                },
                "rule_number": "rule_number1"
            }},
            "chn_index": "CH1",
            "page": "chn_cc",
            "isAiPage": true,
            "rule": {
                "rule_type": "A->B",
                "rule_switch": false,
                "rule_line": {
                    "x1": 0,
                    "y1": 0,
                    "x2": 0,
                    "y2": 0
                },
                "rule_rect": {
                    "x1": 0,
                    "y1": 0,
                    "x2": 0,
                    "y2": 0,
                    "x3": 0,
                    "y3": 0,
                    "x4": 0,
                    "y4": 0
                },
                "rule_number": "rule_number1"
            }
        }},
        "page_type": "ChannelConfig"
    }
}
```

### Setup / Crowd Density Detection

#### Crowd Density Detection

- Source page: `AI/Setup/Crowd Density Detection/API.html`
- Purpose: This API is used for get or set Crowd Density Detection page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/CD/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Setup/Crowd Density Detection/Get.html`
- Purpose: This API is used to get parameter for AI > Setup > Crowd Density Detection  page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/CD/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "ChannelConfig"}
}
```

#### Range

- Source page: `AI/Setup/Crowd Density Detection/Range.html`
- Purpose: This API is used to get parameter range for AI > Setup > Crowd Density Detection  page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/CD/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "ChannelConfig"}
}
```

#### Set

- Source page: `AI/Setup/Crowd Density Detection/Set.html`
- Purpose: This API is used to set parameter for AI > Setup > Crowd Density Detection  page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/CD/Set
HTTP/1.1
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {"CH1": {
            "status": "Online",
            "switch": true,
            "sensitivity": 2,
            "max_pixel": 640,
            "min_pixel": 32,
            "max_detection_num": 50,
            "detection_range": "Customize",
            "rule_info": {"rule_number1": {
                "rule_switch": true,
                "rule_rect": {
                    "x1": 30,
                    "y1": 175,
                    "x2": 240,
                    "y2": 30,
                    "x3": 465,
                    "y3": 30,
                    "x4": 675,
                    "y4": 175,
                    "x5": 675,
                    "y5": 400,
                    "x6": 465,
                    "y6": 545,
                    "x7": 240,
                    "y7": 545,
                    "x8": 30,
                    "y8": 400
                },
                "rule_number": "rule_number1"
            }},
            "chn_index": "CH1",
            "page": "chn_ai_cd",
            "rule": {
                "rule_switch": true,
                "rule_rect": {
                    "x1": 30,
                    "y1": 175,
                    "x2": 240,
                    "y2": 30,
                    "x3": 465,
                    "y3": 30,
                    "x4": 675,
                    "y4": 175,
                    "x5": 675,
                    "y5": 400,
                    "x6": 465,
                    "y6": 545,
                    "x7": 240,
                    "y7": 545,
                    "x8": 30,
                    "y8": 400
                },
                "rule_number": "rule_number1"
            }
        }},
        "page_type": "ChannelConfig"
    }
}
```

### Setup / Face Detection

#### Face Detection

- Source page: `AI/Setup/Face Detection/API.html`
- Purpose: This API is used for get or set Face Detection config parameters。
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/FD/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Setup/Face Detection/Get.html`
- Purpose: This API is used to get parameter for AI > Setup > Face Detection page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/FD/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "ChannelConfig"}
}
```

#### Range

- Source page: `AI/Setup/Face Detection/Range.html`
- Purpose: This API is used to get parameter range for AI > Setup > Face Detection page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/FD/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "ChannelConfig"}
}
```

#### Set

- Source page: `AI/Setup/Face Detection/Set.html`
- Purpose: This API is used to set parameter for AI > Setup > Face Detection page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/FD/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {"CH1": {
            "status": "Online",
            "switch": false,
            "face_attribute": false,
            "snap_mode": "OptimalMode",
            "snap_num": "1",
            "snap_frequency": 2,
            "apply_mode": "FrontalView",
            "roll_range": 30,
            "pitch_range": 30,
            "yaw_range": 45,
            "picture_quality": 100,
            "min_pixel": 64,
            "max_pixel": 640,
            "detection_mode": "StaticMode",
            "rule_info": {"rule_number1": {
                "detection_range": "FullScreen",
                "rule_kind": "Rect",
                "rule_line": {
                    "x1": 322,
                    "y1": 30,
                    "x2": 322,
                    "y2": 545
                },
                "rule_type": "A->B",
                "rule_rect": {
                    "x1": 30,
                    "y1": 30,
                    "x2": 30,
                    "y2": 545,
                    "x3": 675,
                    "y3": 545,
                    "x4": 675,
                    "y4": 30
                }
            }},
            "chn_index": "CH1",
            "page": "chn_fd",
            "rule": {
                "detection_range": "FullScreen",
                "rule_kind": "Rect",
                "rule_line": {
                    "x1": 322,
                    "y1": 30,
                    "x2": 322,
                    "y2": 545
                },
                "rule_type": "A->B",
                "rule_rect": {
                    "x1": 30,
                    "y1": 30,
                    "x2": 30,
                    "y2": 545,
                    "x3": 675,
                    "y3": 545,
                    "x4": 675,
                    "y4": 30
                }
            }
        }},
        "page_type": "ChannelConfig"
    }
}
```

### Setup / Heat Map

#### Heat Map

- Source page: `AI/Setup/Heat Map/API.html`
- Purpose: This API is used to get or set Heat Map configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/HeatMap/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Setup/Heat Map/Get.html`
- Purpose: This API is used to get parameter for AI > Setup > Heat Map page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/HeatMap/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "ChannelConfig"}
}
```

#### Range

- Source page: `AI/Setup/Heat Map/Range.html`
- Purpose: This API is used to get parameter range for AI > Setup > Heat Map page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/HeatMap/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "ChannelConfig"}
}
```

#### Set

- Source page: `AI/Setup/Heat Map/Set.html`
- Purpose: This API is used to set parameter for AI > Setup > Heat Map page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/HeatMap/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {"CH1": {
            "status": "Online",
            "switch": false,
            "rule_info": {"rule_number1": {
                "rule_switch": true,
                "rule_rect": {
                    "x1": 0,
                    "y1": 0,
                    "x2": 704,
                    "y2": 0,
                    "x3": 704,
                    "y3": 576,
                    "x4": 0,
                    "y4": 576
                },
                "rule_number": "rule_number1"
            }},
            "chn_index": "CH1",
            "page": "chn_pd",
            "curPage": "chn_heat_map",
            "rule": {
                "rule_switch": true,
                "rule_rect": {
                    "x1": 0,
                    "y1": 0,
                    "x2": 704,
                    "y2": 0,
                    "x3": 704,
                    "y3": 576,
                    "x4": 0,
                    "y4": 576
                },
                "rule_number": "rule_number1"
            }
        }},
        "page_type": "ChannelConfig"
    }
}
```

### Setup / Human & Vehicle Detection

#### Human & Vehicle Detection

- Source page: `AI/Setup/Human & Vehicle Detection/API.html`
- Purpose: This API is used for get or set PVD page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/PVD/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Setup/Human & Vehicle Detection/Get.html`
- Purpose: This API is used to get parameter for AI > Setup > Human & Vehicle Detection  page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/PVD/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "ChannelConfig"}
}
```

#### Range

- Source page: `AI/Setup/Human & Vehicle Detection/Range.html`
- Purpose: This API is used to get parameter range for AI > Setup > Human & Vehicle Detection  page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/PVD/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "ChannelConfig"}
}
```

#### Set

- Source page: `AI/Setup/Human & Vehicle Detection/Set.html`
- Purpose: This API is used to set parameter for AI > Setup > Human & Vehicle Detection  page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/PVD/Set
HTTP/1.1
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {"CH1": {
            "status": "Online",
            "switch": false,
            "sensitivity": 60,
            "snap_mode": "Default",
            "snap_num": "1",
            "snap_frequency": 2,
            "max_pixel": 640,
            "min_pixel": 64,
            "detection_mode": "MotionMode",
            "detection_type": [
                "Pedestrian",
                "Motor Vehicle",
                "Non-motorized Vehicle"
            ],
            "rule_info": {"rule_number1": {
                "detection_range": "FullScreen",
                "rule_rect": {
                    "x1": 30,
                    "y1": 30,
                    "x2": 30,
                    "y2": 545,
                    "x3": 675,
                    "y3": 545,
                    "x4": 675,
                    "y4": 30
                }
            }},
            "chn_index": "CH1",
            "page": "chn_pd",
            "curPage": "chn_ai_pvd",
            "rule": {
                "detection_range": "FullScreen",
                "rule_rect": {
                    "x1": 30,
                    "y1": 30,
                    "x2": 30,
                    "y2": 545,
                    "x3": 675,
                    "y3": 545,
                    "x4": 675,
                    "y4": 30
                }
            }
        }},
        "page_type": "ChannelConfig"
    }
}
```

### Setup / Intrusion

#### Intrusion

- Source page: `AI/Setup/Intrusion/API.html`
- Purpose: This API is used for get or set AI > Setup > Intrusion parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/Intrusion/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Setup/Intrusion/Get.html`
- Purpose: This API is used to get AI > Setup > Intrusion configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/Intrusion/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{
        "channel":["CH1"],
       "page_type":"ChannelConfig"
    }
}
```

#### Range

- Source page: `AI/Setup/Intrusion/Range.html`
- Purpose: This API is used to get AI > Setup > Intrusion configuration parameter scope.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/Intrusion/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{
        "channel":["CH1"],
        "page_type":"ChannelConfig"
    }
}
```

#### Set

- Source page: `AI/Setup/Intrusion/Set.html`
- Purpose: This API is used to set AI > Setup > Intrusion configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/Intrusion/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {
            "CH1": {
                "switch": true,
                "sensitivity": 50,
                "max_pixel": 640,
                "min_pixel": 64,
                "time_threshold": 0,
                "target_validity": 3,
                "iva_lines": true,
                "detection_type": [],
                "rule_info": {
                    "rule_number1": {
                        "rule_switch": false,
                        "point_num": [
                            3,
                            8
                        ],
                        "rule_rect": {
                            "x1": 0,
                            "y1": 0,
                            "x2": 0,
                            "y2": 0,
                            "x3": 0,
                            "y3": 0,
                            "x4": 0,
                            "y4": 0,
                            "x5": 0,
                            "y5": 0,
                            "x6": 0,
                            "y6": 0,
                            "x7": 0,
                            "y7": 0,
                            "x8": 0,
                            "y8": 0
                        },
                        "rule_number": "rule_number1"
                    },
                    "rule_number2": {
                        "rule_switch": false,
                        "point_num": [
                            3,
                            8
                        ],
                        "rule_rect": {
                            "x1": 0,
                            "y1": 0,
                            "x2": 0,
                            "y2": 0,
                            "x3": 0,
                            "y3": 0,
                            "x4": 0,
                            "y4": 0,
                            "x5": 0,
                            "y5": 0,
                            "x6": 0,
                            "y6": 0,
                            "x7": 0,
                            "y7": 0,
                            "x8": 0,
                            "y8": 0
                        }
                    },
                    "rule_number3": {
                        "rule_switch": false,
                        "point_num": [
                            3,
                            8
                        ],
                        "rule_rect": {
                            "x1": 0,
                            "y1": 0,
                            "x2": 0,
                            "y2": 0,
                            "x3": 0,
                            "y3": 0,
                            "x4": 0,
                            "y4": 0,
                            "x5": 0,
                            "y5": 0,
                            "x6": 0,
                            "y6": 0,
                            "x7": 0,
                            "y7": 0,
                            "x8": 0,
                            "y8": 0
                        }
                    },
                    "rule_number4": {
                        "rule_switch": false,
                        "point_num": [
                            3,
                            8
                        ],
                        "rule_rect": {
                            "x1": 0,
                            "y1": 0,
                            "x2": 0,
                            "y2": 0,
                            "x3": 0,
                            "y3": 0,
                            "x4": 0,
                            "y4": 0,
                            "x5": 0,
                            "y5": 0,
                            "x6": 0,
                            "y6": 0,
                            "x7": 0,
                            "y7": 0,
                            "x8": 0,
                            "y8": 0
                        }
                    }
                },
                "chn_index": "CH1",
                "page": "chn_pid_split",
                "curPage": "chn_ai_intrusion",
                "rule": {
                    "rule_switch": false,
                    "point_num": [
                        3,
                        8
                    ],
                    "rule_rect": {
                        "x1": 0,
                        "y1": 0,
                        "x2": 0,
                        "y2": 0,
                        "x3": 0,
                        "y3": 0,
                        "x4": 0,
                        "y4": 0,
                        "x5": 0,
                        "y5": 0,
                        "x6": 0,
                        "y6": 0,
                        "x7": 0,
                        "y7": 0,
                        "x8": 0,
                        "y8": 0
                    },
                    "rule_number": "rule_number1"
                }
            }
        },
        "page_type": "ChannelConfig"
    }
}
```

### Setup / License Plate Detection

#### License Plate Detection

- Source page: `AI/Setup/License Plate Detection/API.html`
- Purpose: This API is used for get or set LPD page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/LPD/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Setup/License Plate Detection/Get.html`
- Purpose: This API is used to get parameter for AI > Setup > License Plate Detection  page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/LPD/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "ChannelConfig"}
}
```

#### Range

- Source page: `AI/Setup/License Plate Detection/Range.html`
- Purpose: This API is used to get parameter range for AI > Setup > License Plate Detection  page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/LPD/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "ChannelConfig"}
}
```

#### Set

- Source page: `AI/Setup/License Plate Detection/Set.html`
- Purpose: This API is used to set parameter for AI > Setup > License Plate Detection  page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/LPD/Set
HTTP/1.1
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {"CH1": {
            "status": "Online",
            "switch": true,
            "sensitivity": 60,
            "snap_mode": "Default",
            "snap_num": "1",
            "snap_frequency": 2,
            "max_pixel": 640,
            "min_pixel": 64,
            "detection_mode": "MotionMode",
            "detection_type": "EU_Plate",
            "lpd_enhance": false,
            "day_enhance_level": 60,
            "night_enhance_level": 50,
            "rule_info": {"rule_number1": {
                "detection_range": "FullScreen",
                "rule_rect": {
                    "x1": 30,
                    "y1": 30,
                    "x2": 30,
                    "y2": 545,
                    "x3": 675,
                    "y3": 545,
                    "x4": 675,
                    "y4": 30
                }
            }},
            "chn_index": "CH1",
            "page": "chn_pd",
            "curPage": "chn_ai_lpd",
            "rule": {
                "detection_range": "FullScreen",
                "rule_rect": {
                    "x1": 30,
                    "y1": 30,
                    "x2": 30,
                    "y2": 545,
                    "x3": 675,
                    "y3": 545,
                    "x4": 675,
                    "y4": 30
                }
            }
        }},
        "page_type": "ChannelConfig"
    }
}
```

### Setup / Line Crossing Detection

#### Line Crossing Detection

- Source page: `AI/Setup/Line Crossing Detection/API.html`
- Purpose: This API is used to get or set Line Crossing Detection configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/LCD/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Setup/Line Crossing Detection/Get.html`
- Purpose: This API is used to get parameter for AI > Setup > Line Crossing Detection page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/LCD/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "ChannelConfig"}
}
```

#### Range

- Source page: `AI/Setup/Line Crossing Detection/Range.html`
- Purpose: This API is used to get parameter range for AI > Setup > Line Crossing Detection page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/LCD/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "ChannelConfig"}
}
```

#### Set

- Source page: `AI/Setup/Line Crossing Detection/Set.html`
- Purpose: This API is used to set parameter for AI > Setup > Line Crossing Detection page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/LCD/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {"CH1": {
            "status": "Online",
            "switch": true,
            "sensitivity": 2,
            "detection_type": [],
            "rule_info": {
                "rule_number1": {
                    "rule_switch": true,
                    "rule_type": "A<-->B",
                    "rule_line": {
                        "x1": 406,
                        "y1": 165,
                        "x2": 396,
                        "y2": 482
                    }
                },
                "rule_number2": {
                    "rule_switch": true,
                    "rule_type": "A<-->B",
                    "rule_line": {
                        "x1": 263,
                        "y1": 171,
                        "x2": 254,
                        "y2": 483
                    },
                    "rule_number": "rule_number2"
                },
                "rule_number3": {
                    "rule_switch": false,
                    "rule_type": "A->B",
                    "rule_line": {
                        "x1": 0,
                        "y1": 0,
                        "x2": 0,
                        "y2": 0
                    }
                },
                "rule_number4": {
                    "rule_switch": false,
                    "rule_type": "A->B",
                    "rule_line": {
                        "x1": 0,
                        "y1": 0,
                        "x2": 0,
                        "y2": 0
                    }
                }
            },
            "chn_index": "CH1",
            "page": "chn_lcd",
            "rule": {
                "rule_switch": true,
                "rule_type": "A<-->B",
                "rule_line": {
                    "x1": 263,
                    "y1": 171,
                    "x2": 254,
                    "y2": 483
                },
                "rule_number": "rule_number2"
            }
        }},
        "page_type": "ChannelConfig"
    }
}
```

### Setup / Queue Lenght Detection

#### Queue Lenght Detection

- Source page: `AI/Setup/Queue Lenght Detection/API.html`
- Purpose: This API is used for get or set Queue Lenght Detection page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/QD/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Setup/Queue Lenght Detection/Get.html`
- Purpose: This API is used to get parameter for AI > Setup > Queue Lenght Detection  page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/QD/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "ChannelConfig"}
}
```

#### Range

- Source page: `AI/Setup/Queue Lenght Detection/Range.html`
- Purpose: This API is used to get parameter range for AI > Setup > Queue Lenght Detection  page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/QD/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "ChannelConfig"}
}
```

#### Set

- Source page: `AI/Setup/Queue Lenght Detection/Set.html`
- Purpose: This API is used to set parameter for AI > Setup > Queue Lenght Detection  page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/QD/Set
HTTP/1.1
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {"CH1": {
            "status": "Online",
            "switch": true,
            "sensitivity": 2,
            "max_pixel": 640,
            "min_pixel": 32,
            "max_detection_num": 10,
            "max_pro_time": 60,
            "detection_range": "Customize",
            "rule_info": {"rule_number1": {
                "rule_switch": true,
                "rule_rect": {
                    "x1": 30,
                    "y1": 175,
                    "x2": 240,
                    "y2": 30,
                    "x3": 465,
                    "y3": 30,
                    "x4": 675,
                    "y4": 175,
                    "x5": 675,
                    "y5": 400,
                    "x6": 465,
                    "y6": 545,
                    "x7": 240,
                    "y7": 545,
                    "x8": 30,
                    "y8": 400
                },
                "rule_number": "rule_number1"
            }},
            "chn_index": "CH1",
            "page": "chn_ai_qd",
            "rule": {
                "rule_switch": true,
                "rule_rect": {
                    "x1": 30,
                    "y1": 175,
                    "x2": 240,
                    "y2": 30,
                    "x3": 465,
                    "y3": 30,
                    "x4": 675,
                    "y4": 175,
                    "x5": 675,
                    "y5": 400,
                    "x6": 465,
                    "y6": 545,
                    "x7": 240,
                    "y7": 545,
                    "x8": 30,
                    "y8": 400
                },
                "rule_number": "rule_number1"
            }
        }},
        "page_type": "ChannelConfig"
    }
}
```

### Setup / Rare Sound Detection

#### Rare Sound Detection

- Source page: `AI/Setup/Rare Sound Detection/API.html`
- Purpose: This API is used for get or set Rare Sound Detection page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/RSD/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Setup/Rare Sound Detection/Get.html`
- Purpose: This API is used to get parameter for AI > Setup > Rare Sound Detection  page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/RSD/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "ChannelConfig"}
}
```

#### Range

- Source page: `AI/Setup/Rare Sound Detection/Range.html`
- Purpose: This API is used to get parameter range for AI > Setup > Rare Sound Detection  page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/RSD/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "ChannelConfig"}
}
```

#### Set

- Source page: `AI/Setup/Rare Sound Detection/Set.html`
- Purpose: This API is used to set parameter for AI > Setup > Rare Sound Detection  page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/RSD/Set
HTTP/1.1
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {"CH1": {
            "status": "Online",
            "switch": false,
            "sensitivity": 60,
            "detection_type": ["Baby Crying Sound"],
            "chn_index": "CH1",
            "page": "chn_pid",
            "curPage": "chn_ai_rsd"
        }},
        "page_type": "ChannelConfig"
    }
}
```

### Setup / Region_Entrance

#### Region Entrance

- Source page: `AI/Setup/Region_Entrance/API.html`
- Purpose: This API is used for get or set AI > Setup > Region Entrance parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/RegionEntrance/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Setup/Region_Entrance/Get.html`
- Purpose: This API is used to get AI > Setup > Region Entrance configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/RegionEntrance/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel": ["CH1"],
        "page_type": "ChannelConfig"
    }
}
```

#### Range

- Source page: `AI/Setup/Region_Entrance/Range.html`
- Purpose: This API is used to get AI > Setup > Region Entrance configuration parameter scope.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/RegionEntrance/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel": [
            "CH1"
        ],
        "page_type": "ChannelConfig"
    }
}
```

#### Set

- Source page: `AI/Setup/Region_Entrance/Set.html`
- Purpose: This API is used to set AI > Setup > Region Entrance configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/RegionEntrance/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {
            "CH1": {
                "switch": true,
                "sensitivity": 50,
                "max_pixel": 640,
                "min_pixel": 64,
                "target_validity": 3,
                "iva_lines": true,
                "detection_type": [],
                "rule_info": {
                    "rule_number1": {
                        "rule_switch": false,
                        "point_num": [
                            3,
                            8
                        ],
                        "rule_rect": {
                            "x1": 0,
                            "y1": 0,
                            "x2": 0,
                            "y2": 0,
                            "x3": 0,
                            "y3": 0,
                            "x4": 0,
                            "y4": 0,
                            "x5": 0,
                            "y5": 0,
                            "x6": 0,
                            "y6": 0,
                            "x7": 0,
                            "y7": 0,
                            "x8": 0,
                            "y8": 0
                        },
                        "rule_number": "rule_number1"
                    },
                    "rule_number2": {
                        "rule_switch": false,
                        "point_num": [
                            3,
                            8
                        ],
                        "rule_rect": {
                            "x1": 0,
                            "y1": 0,
                            "x2": 0,
                            "y2": 0,
                            "x3": 0,
                            "y3": 0,
                            "x4": 0,
                            "y4": 0,
                            "x5": 0,
                            "y5": 0,
                            "x6": 0,
                            "y6": 0,
                            "x7": 0,
                            "y7": 0,
                            "x8": 0,
                            "y8": 0
                        }
                    },
                    "rule_number3": {
                        "rule_switch": false,
                        "point_num": [
                            3,
                            8
                        ],
                        "rule_rect": {
                            "x1": 0,
                            "y1": 0,
                            "x2": 0,
                            "y2": 0,
                            "x3": 0,
                            "y3": 0,
                            "x4": 0,
                            "y4": 0,
                            "x5": 0,
                            "y5": 0,
                            "x6": 0,
                            "y6": 0,
                            "x7": 0,
                            "y7": 0,
                            "x8": 0,
                            "y8": 0
                        }
                    },
                    "rule_number4": {
                        "rule_switch": false,
                        "point_num": [
                            3,
                            8
                        ],
                        "rule_rect": {
                            "x1": 0,
                            "y1": 0,
                            "x2": 0,
                            "y2": 0,
                            "x3": 0,
                            "y3": 0,
                            "x4": 0,
                            "y4": 0,
                            "x5": 0,
                            "y5": 0,
                            "x6": 0,
                            "y6": 0,
                            "x7": 0,
                            "y7": 0,
                            "x8": 0,
                            "y8": 0
                        }
                    }
                },
                "chn_index": "CH1",
                "page": "chn_pid_split",
                "curPage": "chn_region_entrance",
                "rule": {
                    "rule_switch": false,
                    "point_num": [
                        3,
                        8
                    ],
                    "rule_rect": {
                        "x1": 0,
                        "y1": 0,
                        "x2": 0,
                        "y2": 0,
                        "x3": 0,
                        "y3": 0,
                        "x4": 0,
                        "y4": 0,
                        "x5": 0,
                        "y5": 0,
                        "x6": 0,
                        "y6": 0,
                        "x7": 0,
                        "y7": 0,
                        "x8": 0,
                        "y8": 0
                    },
                    "rule_number": "rule_number1"
                }
            }
        },
        "page_type": "ChannelConfig"
    }
}
```

### Setup / Region_Exiting

#### Region Exiting

- Source page: `AI/Setup/Region_Exiting/API.html`
- Purpose: This API is used for get or set AI > Setup > Region Exiting parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/RegionExiting/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Setup/Region_Exiting/Get.html`
- Purpose: This API is used to get AI > Setup > Region Exiting configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/RegionExiting/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel": [
            "CH1"
        ],
        "page_type": "ChannelConfig"
    }
}
```

#### Range

- Source page: `AI/Setup/Region_Exiting/Range.html`
- Purpose: This API is used to get AI > Setup > Region Exiting configuration parameter scope.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/RegionExiting/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel": [
            "CH1"
        ],
        "page_type": "ChannelConfig"
    }
}
```

#### Set

- Source page: `AI/Setup/Region_Exiting/Set.html`
- Purpose: This API is used to set AI > Setup > Region Exiting configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/RegionExiting/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {
            "CH1": {
                "switch": true,
                "sensitivity": 50,
                "max_pixel": 640,
                "min_pixel": 64,
                "target_validity": 3,
                "iva_lines": true,
                "detection_type": [],
                "rule_info": {
                    "rule_number1": {
                        "rule_switch": false,
                        "point_num": [
                            3,
                            8
                        ],
                        "rule_rect": {
                            "x1": 0,
                            "y1": 0,
                            "x2": 0,
                            "y2": 0,
                            "x3": 0,
                            "y3": 0,
                            "x4": 0,
                            "y4": 0,
                            "x5": 0,
                            "y5": 0,
                            "x6": 0,
                            "y6": 0,
                            "x7": 0,
                            "y7": 0,
                            "x8": 0,
                            "y8": 0
                        },
                        "rule_number": "rule_number1"
                    },
                    "rule_number2": {
                        "rule_switch": false,
                        "point_num": [
                            3,
                            8
                        ],
                        "rule_rect": {
                            "x1": 0,
                            "y1": 0,
                            "x2": 0,
                            "y2": 0,
                            "x3": 0,
                            "y3": 0,
                            "x4": 0,
                            "y4": 0,
                            "x5": 0,
                            "y5": 0,
                            "x6": 0,
                            "y6": 0,
                            "x7": 0,
                            "y7": 0,
                            "x8": 0,
                            "y8": 0
                        }
                    },
                    "rule_number3": {
                        "rule_switch": false,
                        "point_num": [
                            3,
                            8
                        ],
                        "rule_rect": {
                            "x1": 0,
                            "y1": 0,
                            "x2": 0,
                            "y2": 0,
                            "x3": 0,
                            "y3": 0,
                            "x4": 0,
                            "y4": 0,
                            "x5": 0,
                            "y5": 0,
                            "x6": 0,
                            "y6": 0,
                            "x7": 0,
                            "y7": 0,
                            "x8": 0,
                            "y8": 0
                        }
                    },
                    "rule_number4": {
                        "rule_switch": false,
                        "point_num": [
                            3,
                            8
                        ],
                        "rule_rect": {
                            "x1": 0,
                            "y1": 0,
                            "x2": 0,
                            "y2": 0,
                            "x3": 0,
                            "y3": 0,
                            "x4": 0,
                            "y4": 0,
                            "x5": 0,
                            "y5": 0,
                            "x6": 0,
                            "y6": 0,
                            "x7": 0,
                            "y7": 0,
                            "x8": 0,
                            "y8": 0
                        }
                    }
                },
                "chn_index": "CH1",
                "page": "chn_pid_split",
                "curPage": "chn_region_exiting",
                "rule": {
                    "rule_switch": false,
                    "point_num": [
                        3,
                        8
                    ],
                    "rule_rect": {
                        "x1": 0,
                        "y1": 0,
                        "x2": 0,
                        "y2": 0,
                        "x3": 0,
                        "y3": 0,
                        "x4": 0,
                        "y4": 0,
                        "x5": 0,
                        "y5": 0,
                        "x6": 0,
                        "y6": 0,
                        "x7": 0,
                        "y7": 0,
                        "x8": 0,
                        "y8": 0
                    },
                    "rule_number": "rule_number1"
                }
            }
        },
        "page_type": "ChannelConfig"
    }
}
```

### Setup / Stationary Object Detection

#### Stationary Object Detection

- Source page: `AI/Setup/Stationary Object Detection/API.html`
- Purpose: This API is used for get or set SOD page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/SOD/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Setup/Stationary Object Detection/Get.html`
- Purpose: This API is used to get parameter for AI > Setup > Stationary Object Detection page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/SOD/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "ChannelConfig"}
}
```

#### Range

- Source page: `AI/Setup/Stationary Object Detection/Range.html`
- Purpose: This API is used to get parameter range for AI > Setup > Stationary Object Detection page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/SOD/Range
```
```http
HTTP/1.1 200 OK
Content-Type: application/json
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "ChannelConfig"}
}
```
```json
{
    "result": "success",
    "data": {
        "channel_max": 1,
        "channel_info": {
            "type": "object",
            "items": {"CH1": {
                "type": "object",
                "items": {
                    "status": {
                        "description": "Only offline channel has this variable.",
                        "type": "string",
                        "mode": "r",
                        "items": [
                            "Offline",
                            "Online",
                            "Nonsupport"
                        ]
                    },
                    "switch": {"type": "bool"},
                    "sensitivity": {
                        "type": "int32",
                        "items": [
                            1,
                            2,
                            3,
                            4
                        ]
                    },
                    "rule_info": {
                        "type": "object",
                        "items": {
                            "rule_number1": {
                                "type": "object",
                                "items": {
                                    "rule_switch": {"type": "bool"},
                                    "rule_type": {
                                        "type": "string",
                                        "items": [
                                            "Legacy",
                                            "Lost",
                                            "Lost & Legacy"
                                        ]
                                    },
                                    "rule_rect": {
                                        "type": "object",
                                        "items": {
                                            "x1": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 704
                                            },
                                            "x2": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 704
                                            },
                                            "x3": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 704
                                            },
                                            "x4": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 704
                                            },
                                            "y1": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 576
                                            },
                                            "y2": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 576
                                            },
                                            "y3": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 576
                                            },
                                            "y4": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 576
                                            }
                                        }
                                    }
                                }
                            },
                            "rule_number2": {
                                "type": "object",
                                "items": {
                                    "rule_switch": {"type": "bool"},
                                    "rule_type": {
                                        "type": "string",
                                        "items": [
                                            "Legacy",
                                            "Lost",
                                            "Lost & Legacy"
                                        ]
                                    },
                                    "rule_rect": {
                                        "type": "object",
                                        "items": {
                                            "x1": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 704
                                            },
                                            "x2": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 704
                                            },
                                            "x3": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 704
                                            },
                                            "x4": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 704
                                            },
                                            "y1": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 576
                                            },
                                            "y2": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 576
                                            },
                                            "y3": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 576
                                            },
                                            "y4": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 576
                                            }
                                        }
                                    }
                                }
                            },
                            "rule_number3": {
                                "type": "object",
                                "items": {
                                    "rule_switch": {"type": "bool"},
                                    "rule_type": {
                                        "type": "string",
                                        "items": [
                                            "Legacy",
                                            "Lost",
                                            "Lost & Legacy"
                                        ]
                                    },
                                    "rule_rect": {
                                        "type": "object",
                                        "items": {
                                            "x1": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 704
                                            },
                                            "x2": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 704
                                            },
                                            "x3": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 704
                                            },
                                            "x4": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 704
                                            },
                                            "y1": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 576
                                            },
                                            "y2": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 576
                                            },
                                            "y3": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 576
                                            },
                                            "y4": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 576
                                            }
                                        }
                                    }
                                }
                            },
                            "rule_number4": {
                                "type": "object",
                                "items": {
                                    "rule_switch": {"type": "bool"},
                                    "rule_type": {
                                        "type": "string",
                                        "items": [
                                            "Legacy",
                                            "Lost",
                                            "Lost & Legacy"
                                        ]
                                    },
                                    "rule_rect": {
                                        "type": "object",
                                        "items": {
                                            "x1": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 704
                                            },
                                            "x2": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 704
                                            },
                                            "x3": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 704
                                            },
                                            "x4": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 704
                                            },
                                            "y1": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 576
                                            },
                                            "y2": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 576
                                            },
                                            "y3": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 576
                                            },
                                            "y4": {
                                                "type": "int32",
                                                "min": 0,
                                                "max": 576
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }}
        }
    }
}
```

#### Set

- Source page: `AI/Setup/Stationary Object Detection/Set.html`
- Purpose: This API is used to set parameter for AI > Setup > Stationary Object Detection page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/Setup/SOD/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {"CH1": {
            "status": "Online",
            "switch": false,
            "sensitivity": 3,
            "rule_info": {
                "rule_number1": {
                    "rule_switch": false,
                    "rule_type": "Legacy",
                    "rule_rect": {
                        "x1": 231,
                        "y1": 176,
                        "x2": 182,
                        "y2": 501,
                        "x3": 423,
                        "y3": 460,
                        "x4": 419,
                        "y4": 207
                    },
                    "rule_number": "rule_number1"
                },
                "rule_number2": {
                    "rule_switch": false,
                    "rule_type": "Legacy",
                    "rule_rect": {
                        "x1": 0,
                        "y1": 0,
                        "x2": 0,
                        "y2": 0,
                        "x3": 0,
                        "y3": 0,
                        "x4": 0,
                        "y4": 0
                    }
                },
                "rule_number3": {
                    "rule_switch": false,
                    "rule_type": "Legacy",
                    "rule_rect": {
                        "x1": 0,
                        "y1": 0,
                        "x2": 0,
                        "y2": 0,
                        "x3": 0,
                        "y3": 0,
                        "x4": 0,
                        "y4": 0
                    }
                },
                "rule_number4": {
                    "rule_switch": false,
                    "rule_type": "Legacy",
                    "rule_rect": {
                        "x1": 0,
                        "y1": 0,
                        "x2": 0,
                        "y2": 0,
                        "x3": 0,
                        "y3": 0,
                        "x4": 0,
                        "y4": 0
                    }
                }
            },
            "chn_index": "CH1",
            "page": "chn_sod",
            "rule": {
                "rule_switch": false,
                "rule_type": "Legacy",
                "rule_rect": {
                    "x1": 231,
                    "y1": 176,
                    "x2": 182,
                    "y2": 501,
                    "x3": 423,
                    "y3": 460,
                    "x4": 419,
                    "y4": 207
                },
                "rule_number": "rule_number1"
            }
        }},
        "page_type": "ChannelConfig"
    }
}
```

### Snaped_face_or_object

#### Snaped face or object

- Source page: `AI/Snaped_face_or_object/API.html`
- Purpose: Used to obtain AI > Snaped face or object alarm real-time appeal.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/processAlarm/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Snaped_face_or_object/Get.html`
- Purpose: This API is used to get AI > Snaped face or object alarm real-time appeal.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/processAlarm/Get
```
- Validation note: Backend-verified. This is the live face-event endpoint used by your backend poller.
- Request Body (JSON):
```json
{}
```

### Statastics (NVR dedicated) / Cross Counting Statistics

#### Cross Counting Statistics

- Source page: `AI/Statastics (NVR dedicated)/Cross Counting Statistics/API.html`
- Purpose: This API is used to get CC statistics and set CCt parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/CCStatistics/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Statastics (NVR dedicated)/Cross Counting Statistics/Get.html`
- Purpose: This API is used to get CC statistics.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/CCStatistics/Get
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Range

- Source page: `AI/Statastics (NVR dedicated)/Cross Counting Statistics/Range.html`
- Purpose: This API is used to get parameter for AI > Statistics > Cross Counting Statistics page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/CCStatistics/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Search

- Source page: `AI/Statastics (NVR dedicated)/Cross Counting Statistics/Search.html`
- Purpose: This API is used to search CC statistics.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/CCStatistics/Search
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Set

- Source page: `AI/Statastics (NVR dedicated)/Cross Counting Statistics/Set.html`
- Purpose: This API is used to set CCt parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/FCCStatistics/Set
```
- Request Body (JSON): No JSON request body sample was documented on this page.

### Statastics (NVR dedicated) / Face Search

#### Face Search

- Source page: `AI/Statastics (NVR dedicated)/Face Search/API.html`
- Purpose: This API is used to get or search face statistics.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/FaceStatistics/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Statastics (NVR dedicated)/Face Search/Get.html`
- Purpose: This API is used to get face statistics.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/FaceStatistics/Get
```
- Request Body (JSON):
```json
{
	"version":"1.0",
	"data": {
		"MsgId": null,
		"Engine": 0,		
		"StartIndex": 0,
		"Count": 10000 
	}
}
```

#### Search

- Source page: `AI/Statastics (NVR dedicated)/Face Search/Search.html`
- Purpose: This API is used to search face statistics。
- Endpoint:
```http
POST http://000.00.00.000/API/AI/FaceStatistics/Search
```
- Request Body (JSON):
```json
{
	"version":"1.0",
	"data": {
		"MsgId": null,
		"Engine": 0,				
		"StartTime": "2018-10-20 00:00:00",
		"EndTime": "2018-10-28 23:59:59",
		"Chn": [0, 1, 2, 3, 4, 5, 6, 7, 8],  
		"Group": [1, 2, 5, 9, 13] 
	}
}
```

### Statastics (NVR dedicated) / Heat Map Statistics

#### Heat Map Statistics

- Source page: `AI/Statastics (NVR dedicated)/Heat Map Statistics/API.html`
- Purpose: This API is used to get heat map statistics or set alarm attribute detection parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/HeatMapStatistics/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Statastics (NVR dedicated)/Heat Map Statistics/Get.html`
- Purpose: This API is used to get Heat Map statistics.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/HeatMapStatistics/Get
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Range

- Source page: `AI/Statastics (NVR dedicated)/Heat Map Statistics/Range.html`
- Purpose: This API is used to get parameter range for AI >Statistics > Heat Map Statistics page.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/HeatMapStatistics/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Search

- Source page: `AI/Statastics (NVR dedicated)/Heat Map Statistics/Search.html`
- Purpose: This API is used to search alarm attribute detection parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/HeatMapStatistics/Search
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `AI/Statastics (NVR dedicated)/Heat Map Statistics/Set.html`
- Purpose: This API is used to set alarm attribute detection parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/HeatMapStatistics/Set
```
- Request Body (JSON): No JSON request body sample was documented on this page.

### Statastics (NVR dedicated) / Hman & Vehicle Search

#### Hman & Vehicle Search

- Source page: `AI/Statastics (NVR dedicated)/Hman & Vehicle Search/API.html`
- Purpose: This API is used to get object statistics.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/ObjectStatistics/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `AI/Statastics (NVR dedicated)/Hman & Vehicle Search/Get.html`
- Purpose: This API is used to get object statistics.
- Endpoint:
```http
POST http://000.00.00.000/API/AI/ObjectStatistics/Get
```
- Request Body (JSON):
```json
{"version":"1.0",
	"data": {
		"MsgId": null,
		"Engine": 0,			
		"TimePoints":[
			"2020-07-0600:00:00",		
			"2020-07-0700:00:00", 
			"2020-07-0800:00:00",		
			"2020-07-0900:00:00",
			"2020-07-1000:00:00",		
			"2020-07-1100:00:00",
			"2020-07-1200:00:00",		
			"2020-07-1300:00:00"
		],
		"Chn": [0, 1, 2, 3, 4, 5, 6, 7, 8],
		"Type": [1, 2] 
	}
}
```

## Alarm

### CombinationAlarm

#### Combination Alarm

- Source page: `Alarm/CombinationAlarm/API.html`
- Purpose: This API is used to get or set combined alarm parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Combination/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Alarm/CombinationAlarm/Get.html`
- Purpose: This API is used to get Combination Alarm parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Combination/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `Alarm/CombinationAlarm/Range.html`
- Purpose: This API is used to get the combined alarm parameter range.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Combination/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Alarm/CombinationAlarm/Set.html`
- Purpose: This API is used to set combined alarm parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Combination/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"channel_info": {"CH1": {
        "enable_alarm": "Disable",
        "combination_configure": [
            {
                "alarm_type": "AT_MOTION",
                "support_ipc_io": true
            },
            {
                "alarm_type": "AT_MOTION",
                "support_ipc_io": true
            }
        ],
        "buzzer": "0",
        "alarm_out": [],
        "latch_time": "10",
        "record_enable": true,
        "record_channel": ["CH1"],
        "post_recording": "30",
        "show_message": true,
        "send_email": false,
        "full_screen": false,
        "http_listening": false,
        "ftp_picture_upload": true,
        "ftp_video_upload": false,
        "picture_to_cloud": true,
        "video_to_cloud": false,
        "voice_prompts_index": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
        ],
        "voice_prompts_select": [
            1,
            0
        ],
        "voice_prompts_time": [
            {
                "start_hour": 0,
                "start_minute": 0,
                "start_second": 0,
                "end_hour": 23,
                "end_minute": 59,
                "end_second": 59
            },
            {
                "start_hour": 0,
                "start_minute": 0,
                "start_second": 0,
                "end_hour": 23,
                "end_minute": 59,
                "end_second": 59
            },
            {
                "start_hour": 0,
                "start_minute": 0,
                "start_second": 0,
                "end_hour": 23,
                "end_minute": 59,
                "end_second": 59
            },
            {
                "start_hour": 0,
                "start_minute": 0,
                "start_second": 0,
                "end_hour": 23,
                "end_minute": 59,
                "end_second": 59
            },
            {
                "start_hour": 0,
                "start_minute": 0,
                "start_second": 0,
                "end_hour": 23,
                "end_minute": 59,
                "end_second": 59
            },
            {
                "start_hour": 0,
                "start_minute": 0,
                "start_second": 0,
                "end_hour": 23,
                "end_minute": 59,
                "end_second": 59
            },
            {
                "start_hour": 0,
                "start_minute": 0,
                "start_second": 0,
                "end_hour": 23,
                "end_minute": 59,
                "end_second": 59
            },
            {
                "start_hour": 0,
                "start_minute": 0,
                "start_second": 0,
                "end_hour": 23,
                "end_minute": 59,
                "end_second": 59
            },
            {
                "start_hour": 0,
                "start_minute": 0,
                "start_second": 0,
                "end_hour": 23,
                "end_minute": 59,
                "end_second": 59
            },
            {
                "start_hour": 0,
                "start_minute": 0,
                "start_second": 0,
                "end_hour": 23,
                "end_minute": 59,
                "end_second": 59
            },
            {
                "start_hour": 0,
                "start_minute": 0,
                "start_second": 0,
                "end_hour": 23,
                "end_minute": 59,
                "end_second": 59
            },
            {
                "start_hour": 0,
                "start_minute": 0,
                "start_second": 0,
                "end_hour": 23,
                "end_minute": 59,
                "end_second": 59
            }
        ],
        "copy_ch": "all",
        "chn_index": "CH1"
    }}}
}
```

### CrossCounting

#### Cross Counting

- Source page: `Alarm/CrossCounting/API.html`
- Purpose: This API is used to get or set the line crossing statistics alarm configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/CC/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Alarm/CrossCounting/Get.html`
- Purpose: This API is used to get Alarm > Cross Counting configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/CC/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{
        "page_type":"AlarmConfig"
    }
}
```

#### Range

- Source page: `Alarm/CrossCounting/Range.html`
- Purpose: This API is used to get the Alarm > Cross Counting configuration parameter range.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/CC/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{
        "page_type":"AlarmConfig"
    }
}
```

#### Set

- Source page: `Alarm/CrossCounting/Set.html`
- Purpose: This API is used to set Alarm > Cross Counting configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/Output/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{
        "channel_info":{
            "CH6":{
                "buzzer":"0",
                "alarm_out":[

                ],
                "latch_time":"10",
                "record_enable":true,
                "http_listening":false,
                "record_channel":[
                    "CH6"
                ],
                "post_recording":"30",
                "show_message":true,
                "send_email":true,
                "full_screen":false,
                "ftp_picture_upload":true,
                "ftp_video_upload":false,
                "picture_to_cloud":true,
                "video_to_cloud":false,
                "voice_prompts_index":[
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0
                ],
                "voice_prompts_select":[
                    1,
                    0
                ],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all",
                "chn_index":"CH6"
            }
        },
        "page_type":"AlarmConfig"
    }
}
```

### Disarming

#### Disarming

- Source page: `Alarm/Disarming/API.html`
- Purpose: This API is used to get or set one key disarm parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Disarming/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Alarm/Disarming/Get.html`
- Purpose: This API is used to get Alarm > Disarming parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Disarming/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `Alarm/Disarming/Range.html`
- Purpose: This API is used to get Alarm > Disarming parameter range.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Disarming/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Alarm/Disarming/Set.html`
- Purpose: This API is used to set Alarm > Disarming parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Disarming/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "disarming": false,
        "action": {
            "buzzer": false,
            "alarm_out": false,
            "show_message": true,
            "send_email": true,
            "full_screen": false,
            "voice_prompts": false,
            "event_push_platform": false,
            "mobile_push": false
        },
        "disarming_channel": [
            "CH1",
            "CH2",
            "CH3",
            "CH4",
            "CH5",
            "CH6",
            "CH7",
            "CH8",
            "CH9",
            "CH10",
            "CH11",
            "CH12",
            "CH13",
            "CH14",
            "CH15",
            "CH16"
        ],
        "channel_info": {
            "CH1": {
                "disarming_schedule": [
                    {
                        "schedule_type": "Disarming",
                        "week": [
                            {
                                "day": "Sun",
                                "time": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
                            },
                            {
                                "day": "Mon",
                                "time": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
                            },
                            {
                                "day": "Tue",
                                "time": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
                            },
                            {
                                "day": "Wed",
                                "time": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
                            },
                            {
                                "day": "Thu",
                                "time": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
                            },
                            {
                                "day": "Fri",
                                "time": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
                            },
                            {
                                "day": "Sat",
                                "time": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
                            }
                        ]
                    }
                ]
            }
        },
        "schedule_chn_index": "CH1",
        "chn_index": "CH1",
        "selectedChn": "CH1",
        "schedule": {
            "data": [
                [
                    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
                ]
            ],
            "colors": [
                "#50A037"
            ],
            "words": [
                "Disarming"
            ],
            "titlewords": [
                "Disarming"
            ],
            "cells": {
                "width": "20px",
                "height": "20px"
            },
            "weeks": [
                "SUN",
                "MON",
                "TUE",
                "WED",
                "THU",
                "FRI",
                "SAT"
            ],
            "radio": -1,
            "defaultSelType": {
                "default": 0
            }
        }
    }
}
```

### Exception

#### Exception

- Source page: `Alarm/Exception/API.html`
- Purpose: This API is used fo get or set Exception parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Exception/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Alarm/Exception/Get.html`
- Purpose: This API is used to get parameter for Alarm > Exception.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Exception/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data": {}
}
```

#### Range

- Source page: `Alarm/Exception/Range.html`
- Purpose: This API is used to get the parameter range of Alarm > Exception.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Exception/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data": {}
}
```

#### Set

- Source page: `Alarm/Exception/Set.html`
- Purpose: This API is used to set parameter for Alarm>Exception.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Exception/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "exception_info":
        {
            "video_loss":
            {
                "switch":true,
                "buzzer":"0",
                "alarm_out":[],
                "latch_time":"10",
                "show_message":true,
                "send_email":false,
                "voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],"voice_prompts_select":[1,0],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }],
                    "exParam_index":"video_loss"
            },
            "disk_error":
            {
                "switch":true,
                "buzzer":"0",
                "alarm_out":[],
                "latch_time":"10",
                "show_message":true,
                "send_email":false,
                "voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],"voice_prompts_select":[1,0],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }]
                },
                "no_space_on_disk":
                {
                    "switch":true,
                    "buzzer":"0",
                    "alarm_out":[],
                    "latch_time":"10",
                    "show_message":true,
                    "send_email":false,
                    "voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],
                    "voice_prompts_select":[1,0],"voice_prompts_time":[
                        {"start_hour":0,"start_minute":0,
                            "start_second":0,
                            "end_hour":23,
                            "end_minute":59,
                            "end_second":59
                        },
                        {
                            "start_hour":0,
                            "start_minute":0,
                            "start_second":0,
                            "end_hour":23,
                            "end_minute":59,
                            "end_second":59
                        },
                        {
                            "start_hour":0,
                            "start_minute":0,
                            "start_second":0,
                            "end_hour":23,
                            "end_minute":59,
                            "end_second":59
                        },
                        {
                            "start_hour":0,
                            "start_minute":0,
                            "start_second":0,
                            "end_hour":23,
                            "end_minute":59,
                            "end_second":59
                        },
                        {
                            "start_hour":0,
                            "start_minute":0,
                            "start_second":0,
                            "end_hour":23,
                            "end_minute":59,
                            "end_second":59
                        },
                        {
                            "start_hour":0,
                            "start_minute":0,
                            "start_second":0,
                            "end_hour":23,
                            "end_minute":59,
                            "end_second":59
                        },
                        {
                            "start_hour":0,
                            "start_minute":0,
                            "start_second":0,
                            "end_hour":23,
                            "end_minute":59,
                            "end_second":59
                        },
                        {
                            "start_hour":0,
                            "start_minute":0,
                            "start_second":0,
                            "end_hour":23,
                            "end_minute":59,
                            "end_second":59
                        },
                        {
                            "start_hour":0,
                            "start_minute":0,
                            "start_second":0,
                            "end_hour":23,
                            "end_minute":59,
                            "end_second":59
                        },
                        {
                            "start_hour":0,
                            "start_minute":0,
                            "start_second":0,
                            "end_hour":23,
                            "end_minute":59,
                            "end_second":59
                        },
                        {
                            "start_hour":0,
                            "start_minute":0,
                            "start_second":0,
                            "end_hour":23,
                            "end_minute":59,
                            "end_second":59
                        },
                        {
                            "start_hour":0,
                            "start_minute":0,
                            "start_second":0,
                            "end_hour":23,
                            "end_minute":59,
                            "end_second":59
                        }
                    ]
                }
        }
    }
}
```

### FaceDetection

#### Face Detection

- Source page: `Alarm/FaceDetection/API.html`
- Purpose: This API is used to get or set face detection configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/FD/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Alarm/FaceDetection/Get.html`
- Purpose: This API is used to get Alarm > Face Detection parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/FD/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{
        "page_type":"AlarmConfig"
    }
}
```

#### Range

- Source page: `Alarm/FaceDetection/Range.html`
- Purpose: This API is used to get Alarm > Face Detection parameter range.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/FD/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Alarm/FaceDetection/Set.html`
- Purpose: This API is used to set Alarm > Face Detection parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/FD/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{
        "channel_info":{
            "CH5":{
                "buzzer":"0",
                "alarm_out":[

                ],
                "latch_time":"10",
                "record_enable":true,
                "http_listening":false,
                "record_channel":[
                    "CH5"
                ],
                "post_recording":"30",
                "show_message":true,
                "send_email":true,
                "full_screen":false,
                "ftp_picture_upload":true,
                "ftp_video_upload":false,
                "picture_to_cloud":true,
                "video_to_cloud":false,
                "voice_prompts_index":[
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0
                ],
                "voice_prompts_select":[
                    1,
                    0
                ],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all",
                "chn_index":"CH5"
            }
        },
        "page_type":"AlarmConfig"
    }
}
```

### Flood-light

#### Flood-light

- Source page: `Alarm/Flood-light/API.html`
- Purpose: This API is used for get or set flood light parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Deterrence/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Default

- Source page: `Alarm/Flood-light/Default.html`
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Deterrence/Default
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "channel":["CH1"]
    }
}
```

#### Get

- Source page: `Alarm/Flood-light/Get.html`
- Purpose: This API is used to get parameter for Alarm > Flood-light.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Deterrence/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
        {
            "page_type":"ChannelConfig"
        }
}
```

#### Range

- Source page: `Alarm/Flood-light/Range.html`
- Purpose: This API is used to get the parameter range of Alarm > Floodlight.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Deterrence/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Alarm/Flood-light/Set.html`
- Purpose: This API is used to set parameter for Alarm > Flood-light.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Deterrence/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {"CH1": {
            "flood_light_switch": true,
            "bright_time": 60,
            "flood_light_mode": "Warninglight",
            "strobe_frequency": "Middle",
            "param_video": {
                "show": false,
                "disable": true
            },
            "flood_light_disable": false,
            "warning_light_disable": false,
            "chn_index": "CH1",
            "page": "chn_floodlight"
        }},
        "page_type": "ChannelConfig"
    }
}
```

### IntelligentAnalysis

#### Intelligent Analysis

- Source page: `Alarm/IntelligentAnalysis/API.html`
- Purpose: This API is used to get or set smart analysis configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/Intelligent/IntelligentAnalysis/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Alarm/IntelligentAnalysis/Get.html`
- Purpose: This API is used to get Alarm > Intelligent Analysis configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/Intelligent/IntelligentAnalysis/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
    }
}
```

#### Range

- Source page: `Alarm/IntelligentAnalysis/Range.html`
- Purpose: This API is used to get Alarm > Intelligent Analysis configuration parameter scope.
- Endpoint:
```http
POST http://000.00.00.000/API/Intelligent/IntelligentAnalysis/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Alarm/IntelligentAnalysis/Set.html`
- Purpose: This API is used to set Alarm > Intelligent Analysis configuration parameters.
- Endpoint: Not explicitly documented in a request sample on this page.
- Request Body (JSON): No JSON request body sample was documented on this page.

### IO Alarm

#### IO Alarm

- Source page: `Alarm/IO Alarm/API.html`
- Purpose: This API is used for get or set IO Alarm parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/IO/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Alarm/IO Alarm/Get.html`
- Purpose: This API is used to get parameter for Alarm > IO Alarm.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/IO/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Range

- Source page: `Alarm/IO Alarm/Range.html`
- Purpose: This API is used to get the parameter range of Alarm > IO Alarm.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/IO/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Get

- Source page: `Alarm/IO Alarm/Set.html`
- Purpose: This API is used to get parameter for Alarm > IO Alarm .
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/IO/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "channel_info":
        {
            "Local<-1":
            {
                "alarm_type":"NormallyOpen",
                "buzzer":"0",
                "latch_time":"10",
                "post_recording":"30",
                "show_message":true,
                "send_email":false,
                "full_screen":false,
                "ftp_picture_upload":false,
                "ftp_video_upload":false,
                "http_listening":false,
                "picture_to_cloud":false,
                "video_to_cloud":false,
                "alarm_out":[],
                "channel":["CH1"],
                "voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],"voice_prompts_select":[1,0],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }],
                "copy_ch":"all",
                "chn_index":"Local<-1"
            },
            "Local<-2":
            {
                "alarm_type":"NormallyOpen",
                "buzzer":"0",
                "latch_time":"10",
                "post_recording":"30",
                "show_message":true,
                "send_email":false,
                "full_screen":false,
                "ftp_picture_upload":false,
                "ftp_video_upload":false,
                "http_listening":false,
                "picture_to_cloud":false,
                "video_to_cloud":false,
                "alarm_out":[],
                "channel":["CH2"],
                "voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],"voice_prompts_select":[0,0],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }],
                "copy_ch":"all"
            },
            "Local<-3":
            {
                "alarm_type":"NormallyOpen",
                "buzzer":"0",
                "latch_time":"10",
                "post_recording":"30",
                "show_message":true,
                "send_email":false,
                "full_screen":false,
                "ftp_picture_upload":false,
                "ftp_video_upload":false,
                "http_listening":false,
                "picture_to_cloud":false,
                "video_to_cloud":false,
                "alarm_out":[],
                "channel":["CH3"],
                "voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],"voice_prompts_select":[1,0],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }],
                "copy_ch":"all"
            },
            "Local<-4":
            {
                "alarm_type":"NormallyOpen",
                "buzzer":"0",
                "latch_time":"10",
                "post_recording":"30",
                "show_message":true,
                "send_email":false,
                "full_screen":false,
                "ftp_picture_upload":false,
                "ftp_video_upload":false,
                "http_listening":false,
                "picture_to_cloud":false,
                "video_to_cloud":false,
                "alarm_out":[],
                "channel":["CH4"],
                "voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],"voice_prompts_select":[0,0],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,"start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all"
            },
            "Local<-5":
            {
                "alarm_type":"NormallyOpen",
                "buzzer":"0",
                "latch_time":"10",
                "post_recording":"30",
                "show_message":true,
                "send_email":false,
                "full_screen":false,
                "ftp_picture_upload":false,
                "ftp_video_upload":false,
                "http_listening":false,
                "picture_to_cloud":false,
                "video_to_cloud":false,
                "alarm_out":[],
                "channel":["CH5"],
                "voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],"voice_prompts_select":[1,0],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all"
            },
            "Local<-6":
            {
                "alarm_type":"NormallyOpen",
                "buzzer":"0",
                "latch_time":"10",
                "post_recording":"30",
                "show_message":true,
                "send_email":false,
                "full_screen":false,
                "ftp_picture_upload":false,
                "ftp_video_upload":false,
                "http_listening":false,
                "picture_to_cloud":false,
                "video_to_cloud":false,
                "alarm_out":[],
                "channel":["CH6"],
                "voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],"voice_prompts_select":[0,0],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all"
            },
            "Local<-7":
            {
                "alarm_type":"NormallyOpen",
                "buzzer":"0",
                "latch_time":"10",
                "post_recording":"30",
                "show_message":true,
                "send_email":false,
                "full_screen":false,
                "ftp_picture_upload":false,
                "ftp_video_upload":false,
                "http_listening":false,
                "picture_to_cloud":false,
                "video_to_cloud":false,
                "alarm_out":[],
                "channel":["CH7"],
                "voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],"voice_prompts_select":[1,0],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all"
            },
            "Local<-8":
            {
                "alarm_type":"NormallyOpen",
                "buzzer":"0",
                "latch_time":"10",
                "post_recording":"30",
                "show_message":true,
                "send_email":false,
                "full_screen":false,
                "ftp_picture_upload":false,
                "ftp_video_upload":false,
                "http_listening":false,
                "picture_to_cloud":false,
                "video_to_cloud":false,
                "alarm_out":[],
                "channel":["CH8"],
                "voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],"voice_prompts_select":[0,0],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all"
            },
            "Local<-9":
            {
                "alarm_type":"NormallyOpen",
                "buzzer":"0",
                "latch_time":"10",
                "post_recording":"30",
                "show_message":true,
                "send_email":false,
                "full_screen":false,
                "ftp_picture_upload":false,
                "ftp_video_upload":false,
                "http_listening":false,
                "picture_to_cloud":false,
                "video_to_cloud":false,
                "alarm_out":[],
                "channel":["CH9"],
                "voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],"voice_prompts_select":[1,0],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all"
            },
            "Local<-10":
            {
                "alarm_type":"NormallyOpen",
                "buzzer":"0",
                "latch_time":"10",
                "post_recording":"30",
                "show_message":true,
                "send_email":false,
                "full_screen":false,
                "ftp_picture_upload":false,
                "ftp_video_upload":false,
                "http_listening":false,
                "picture_to_cloud":false,
                "video_to_cloud":false,
                "alarm_out":[],
                "channel":["CH10"],
                "voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],"voice_prompts_select":[0,0],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all"
            },
            "Local<-11":
            {
                "alarm_type":"NormallyOpen",
                "buzzer":"0",
                "latch_time":"10",
                "post_recording":"30",
                "show_message":true,
                "send_email":false,
                "full_screen":false,
                "ftp_picture_upload":false,
                "ftp_video_upload":false,
                "http_listening":false,
                "picture_to_cloud":false,
                "video_to_cloud":false,
                "alarm_out":[],
                "channel":["CH11"],
                "voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],"voice_prompts_select":[1,0],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all"
            },
            "Local<-12":
            {
                "alarm_type":"NormallyOpen",
                "buzzer":"0",
                "latch_time":"10",
                "post_recording":"30",
                "show_message":true,
                "send_email":false,
                "full_screen":false,
                "ftp_picture_upload":false,
                "ftp_video_upload":false,
                "http_listening":false,
                "picture_to_cloud":false,
                "video_to_cloud":false,
                "alarm_out":[],
                "channel":["CH12"],
                "voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],"voice_prompts_select":[0,0],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all"
            },
            "Local<-13":
            {
                "alarm_type":"NormallyOpen",
                "buzzer":"0",
                "latch_time":"10",
                "post_recording":"30",
                "show_message":true,
                "send_email":false,
                "full_screen":false,
                "ftp_picture_upload":false,
                "ftp_video_upload":false,
                "http_listening":false,
                "picture_to_cloud":false,
                "video_to_cloud":false,
                "alarm_out":[],
                "channel":["CH13"],
                "voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],"voice_prompts_select":[1,0],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all"
            },
            "Local<-14":
            {
                "alarm_type":"NormallyOpen",
                "buzzer":"0",
                "latch_time":"10",
                "post_recording":"30",
                "show_message":true,
                "send_email":false,
                "full_screen":false,
                "ftp_picture_upload":false,
                "ftp_video_upload":false,
                "http_listening":false,
                "picture_to_cloud":false,
                "video_to_cloud":false,
                "alarm_out":[],
                "channel":["CH14"],
                "voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],"voice_prompts_select":[0,0],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all"
            },
            "Local<-15":
            {
                "alarm_type":"NormallyOpen",
                "buzzer":"0",
                "latch_time":"10",
                "post_recording":"30",
                "show_message":true,
                "send_email":false,
                "full_screen":false,
                "ftp_picture_upload":false,
                "ftp_video_upload":false,
                "http_listening":false,
                "picture_to_cloud":false,
                "video_to_cloud":false,
                "alarm_out":[],
                "channel":["CH15"],
                "voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],"voice_prompts_select":[1,0],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all"
            },
            "Local<-16":
            {
                "alarm_type":"NormallyOpen",
                "buzzer":"0",
                "latch_time":"10",
                "post_recording":"30",
                "show_message":true,
                "send_email":false,
                "full_screen":false,
                "ftp_picture_upload":false,
                "ftp_video_upload":false,
                "http_listening":false,
                "picture_to_cloud":false,
                "video_to_cloud":false,
                "alarm_out":[],
                "channel":["CH16"],
                "voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],"voice_prompts_select":[0,0],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all"
            },
            "IP_CH5<-1":
            {
                "alarm_type":"Off",
                "buzzer":"0",
                "latch_time":"10",
                "post_recording":"30",
                "show_message":true,
                "send_email":false,
                "full_screen":false,
                "ftp_picture_upload":false,
                "ftp_video_upload":false,
                "http_listening":false,
                "picture_to_cloud":false,
                "video_to_cloud":false,
                "alarm_out":[],
                "channel":["CH5"],
                "voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],"voice_prompts_select":[1,0],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all"
            }
        }
    }
}
```

### Line Crossing Detection

#### Line Crossing Detection

- Source page: `Alarm/Line Crossing Detection/API.html`
- Purpose: This API is used for get or set LCD config parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/LCD/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Alarm/Line Crossing Detection/Get.html`
- Purpose: This API is used to get parameter for Alarm > Line Crossing Detection.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/LCD/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "page_type":"AlarmConfig"
    }
}
```

#### Range

- Source page: `Alarm/Line Crossing Detection/Range.html`
- Purpose: This API is used to get the parameter range of Alarm > Line Crossing Detection.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/LCD/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "page_type":"AlarmConfig"
    }
}
```

#### Set

- Source page: `Alarm/Line Crossing Detection/Set.html`
- Purpose: This API is used to set parameter for Alarm > Line Crossing Detection .
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/LCD/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "channel_info":
        {
            "CH4":
            {
                "buzzer":"0",
                "alarm_out":[],
                "latch_time":"10",
                "record_enable":true,
                "record_channel":["CH4"],"post_recording":"30",
                "show_message":false,
                "send_email":false,
                "full_screen":false,"ftp_picture_upload":false,"ftp_video_upload":false,"picture_to_cloud":false,"video_to_cloud":false,"http_listening":false,"voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],
                "voice_prompts_select":[0,0],"voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all",
                "chn_index":"CH4"
            },
            "CH18":
            {
                "buzzer":"0",
                "alarm_out":[],
                "latch_time":"10",
                "record_enable":true,
                "record_channel":["CH18"],"post_recording":"30",
                "show_message":false,
                "send_email":false,
                "full_screen":false,"ftp_picture_upload":false,"ftp_video_upload":false,"picture_to_cloud":false,"video_to_cloud":false,"http_listening":false,"voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],
                "voice_prompts_select":[0,0],"voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all"
            }
        },
        "page_type":"AlarmConfig"
    }
}
```

### LinkageSchedule

#### Linkage Schedule

- Source page: `Alarm/LinkageSchedule/API.html`
- Purpose: This API is used to get or set linkage schedule parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Schedule/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Alarm/LinkageSchedule/Get.html`
- Purpose: This API is used to get Alarm > Linkage Schedule parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Schedule/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "page_type": "AlarmConfig",
        "channel":["CH1"]
    }
}
```

#### Range

- Source page: `Alarm/LinkageSchedule/Range.html`
- Purpose: This API is used to get Alarm > Linkage Schedule parameter range.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Schedule/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data":{
        "page_type":" FloodLight",
        "channel":["CH1"]
    }
}
```

#### Set

- Source page: `Alarm/LinkageSchedule/Set.html`
- Purpose: This API is used to set Alarm > Linkage Schedule parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Schedule/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
	"data": {
		"channel_info": {
			"CH1": {
				"schedule": 
				[
					{
						"schedule_type": "Motion",
                        "week": 
						[
                            {
                                "day": "Sun",
                                "time": [1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1]
                            },
							{
                                "day": "Mon",
                                "time": [1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1]
                            },
							{
                                "day": "Tue",
                                "time": [1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1]
                            },
							{
                                "day": "Wed",
                                "time": [1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1]
                            },
							{
                                "day": "Thu",
                                "time": [1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1]
                            },
							{
                                "day": "Fri",
                                "time": [1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1]
                            },
							{
                                "day": "Sat",
                                "time": [1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1]
                            },
						]
					}
				]
			}
		}
	}
}
```

### Motion Alarm

#### Motion Alarm

- Source page: `Alarm/Motion Alarm/API.html`
- Purpose: This API is used for get or set Motion Alarm parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Motion/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Alarm/Motion Alarm/Get.html`
- Purpose: This API is used to get parameter for Alarm > MOtion Alarm.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Motion/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0","data":{
        "page_type":"AlarmConfig"
    }
}
```

#### Range

- Source page: `Alarm/Motion Alarm/Range.html`
- Purpose: This API is used to get the parameter range of Alarm > MOtion Alarm.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Motion/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0","data":{
        "page_type":"AlarmConfig"
    }
}
```

#### Set

- Source page: `Alarm/Motion Alarm/Set.html`
- Purpose: This API is used to set parameter for Alarm > Motion Alarm.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Motion/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {
            "CH1": {
                "buzzer": "0",
                "alarm_out": [],
                "latch_time": "10",
                "record_enable": true,
                "record_channel": ["CH1"],
                "http_listening": false,
                "post_recording": "30",
                "show_message": true,
                "send_email": false,
                "full_screen": false,
                "ftp_picture_upload": true,
                "ftp_video_upload": false,
                "picture_to_cloud": true,
                "video_to_cloud": false,
                "voice_prompts_index": [
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0
                ],
                "voice_prompts_select": [
                    1,
                    0
                ],
                "voice_prompts_time": [
                    {
                        "start_hour": 0,
                        "start_minute": 0,
                        "start_second": 0,
                        "end_hour": 23,
                        "end_minute": 59,
                        "end_second": 59
                    },
                    {
                        "start_hour": 0,
                        "start_minute": 0,
                        "start_second": 0,
                        "end_hour": 23,
                        "end_minute": 59,
                        "end_second": 59
                    },
                    {
                        "start_hour": 0,
                        "start_minute": 0,
                        "start_second": 0,
                        "end_hour": 23,
                        "end_minute": 59,
                        "end_second": 59
                    },
                    {
                        "start_hour": 0,
                        "start_minute": 0,
                        "start_second": 0,
                        "end_hour": 23,
                        "end_minute": 59,
                        "end_second": 59
                    },
                    {
                        "start_hour": 0,
                        "start_minute": 0,
                        "start_second": 0,
                        "end_hour": 23,
                        "end_minute": 59,
                        "end_second": 59
                    },
                    {
                        "start_hour": 0,
                        "start_minute": 0,
                        "start_second": 0,
                        "end_hour": 23,
                        "end_minute": 59,
                        "end_second": 59
                    },
                    {
                        "start_hour": 0,
                        "start_minute": 0,
                        "start_second": 0,
                        "end_hour": 23,
                        "end_minute": 59,
                        "end_second": 59
                    },
                    {
                        "start_hour": 0,
                        "start_minute": 0,
                        "start_second": 0,
                        "end_hour": 23,
                        "end_minute": 59,
                        "end_second": 59
                    },
                    {
                        "start_hour": 0,
                        "start_minute": 0,
                        "start_second": 0,
                        "end_hour": 23,
                        "end_minute": 59,
                        "end_second": 59
                    },
                    {
                        "start_hour": 0,
                        "start_minute": 0,
                        "start_second": 0,
                        "end_hour": 23,
                        "end_minute": 59,
                        "end_second": 59
                    },
                    {
                        "start_hour": 0,
                        "start_minute": 0,
                        "start_second": 0,
                        "end_hour": 23,
                        "end_minute": 59,
                        "end_second": 59
                    },
                    {
                        "start_hour": 0,
                        "start_minute": 0,
                        "start_second": 0,
                        "end_hour": 23,
                        "end_minute": 59,
                        "end_second": 59
                    }
                ],
                "copy_ch": "all",
                "chn_index": "CH1"
            }
        },
        "page_type": "AlarmConfig"
    }
}
```

### Occlusion Detection

#### Occlusion Detection

- Source page: `Alarm/Occlusion Detection/API.html`
- Purpose: This API is used for get or set OcclusionDetectionconfig parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/OcclusionDetection/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Alarm/Occlusion Detection/Get.html`
- Purpose: This API is used to get Alarm > Occlusion Detection config parameter.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/OcclusionDetection/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "page_type":"AlarmConfig"
    }
}
```

#### Range

- Source page: `Alarm/Occlusion Detection/Range.html`
- Purpose: This API is used to get the parameter range of Alarm > Occlusion Detection.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/OcclusionDetection/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Set

- Source page: `Alarm/Occlusion Detection/Set.html`
- Purpose: This API is used to set parameter for Alarm > Occlusion Detection.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/OcclusionDetection/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "channel_info":
        {
            "CH4":
            {
                "buzzer":"0",
                "alarm_out":[],
                "latch_time":"10",
                "record_enable":true,
                "record_channel":["CH4"],"post_recording":"30",
                "show_message":false,
                "send_email":false,
                "full_screen":false,"ftp_picture_upload":false,"ftp_video_upload":false,"picture_to_cloud":false,"video_to_cloud":false,"http_listening":false,"voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],
                "voice_prompts_select":[0,0],"voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all",
                "chn_index":"CH4"
            },
            "CH18":
            {
                "buzzer":"0",
                "alarm_out":[],
                "latch_time":"10",
                "record_enable":true,
                "record_channel":["CH18"],"post_recording":"30",
                "show_message":false,
                "send_email":false,
                "full_screen":false,"ftp_picture_upload":false,"ftp_video_upload":false,"picture_to_cloud":false,"video_to_cloud":false,"http_listening":false,"voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],
                "voice_prompts_select":[0,0],"voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all"
            }
        },
        "page_type":"AlarmConfig"
    }
}
```

### PedestrianDetection

#### Pedestrian Detection

- Source page: `Alarm/PedestrianDetection/API.html`
- Purpose: This API is used to get or set pedestrian detection configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/PD/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Alarm/PedestrianDetection/Get.html`
- Purpose: This API is used to get Alarm > Pedestrian Detection configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/PD/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{
        "page_type":"AlarmConfig"
    }
}
```

#### Range

- Source page: `Alarm/PedestrianDetection/Range.html`
- Purpose: This API is used to get Alarm > Pedestrian Detection configuration parameters range.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/PD/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "AlarmConfig"}
}
```

#### Set

- Source page: `Alarm/PedestrianDetection/Set.html`
- Purpose: This API is used to set Alarm > Pedestrian Detection configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/PD/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{
        "channel_info":{
            "CH6":{
                "buzzer":"0",
                "alarm_out":[

                ],
                "latch_time":"10",
                "record_enable":true,
                "http_listening":false,
                "record_channel":[
                    "CH6",
                    "CH5"
                ],
                "post_recording":"30",
                "show_message":true,
                "send_email":true,
                "full_screen":false,
                "ftp_picture_upload":true,
                "ftp_video_upload":false,
                "picture_to_cloud":true,
                "video_to_cloud":false,
                "voice_prompts_index":[
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0
                ],
                "voice_prompts_select":[
                    1,
                    0
                ],
                "voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all",
                "chn_index":"CH6"
            }
        },
        "page_type":"AlarmConfig"
    }
}
```

### Perimeter Intrusion Detection

#### Perimeter Intrusion Detection

- Source page: `Alarm/Perimeter Intrusion Detection/API.html`
- Purpose: This API is used for get or set PID parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/PID/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Alarm/Perimeter Intrusion Detection/Get.html`
- Purpose: This API is used to get parameter for Alarm > Perimeter Intrusion Detection.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/PID/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "page_type":"AlarmConfig"
    }
}
```

#### Range

- Source page: `Alarm/Perimeter Intrusion Detection/Range.html`
- Purpose: This API is used to get the parameter range of Alarm > Perimeter Intrusion Detection.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/PID/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "page_type":"AlarmConfig"
    }
}
```

#### Set

- Source page: `Alarm/Perimeter Intrusion Detection/Set.html`
- Purpose: This API is used to set parameter for Alarm > Perimeter Intrusion Detection.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/PID/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "channel_info":
        {
            "CH4":
            {
                "buzzer":"0",
                "alarm_out":[],
                "latch_time":"10",
                "record_enable":true,
                "record_channel":["CH4"],"post_recording":"30",
                "show_message":false,
                "send_email":false,
                "full_screen":false,"ftp_picture_upload":false,"ftp_video_upload":false,"picture_to_cloud":false,"video_to_cloud":false,"http_listening":false,"voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],
                "voice_prompts_select":[0,0],"voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all",
                "chn_index":"CH4"
            },
            "CH18":
            {
                "buzzer":"0",
                "alarm_out":[],
                "latch_time":"10",
                "record_enable":true,
                "record_channel":["CH18"],"post_recording":"30",
                "show_message":false,
                "send_email":false,
                "full_screen":false,"ftp_picture_upload":false,"ftp_video_upload":false,"picture_to_cloud":false,"video_to_cloud":false,"http_listening":false,"voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],
                "voice_prompts_select":[0,0],"voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all"
            }
        },
        "page_type":"AlarmConfig"
    }
}
```

### PIR

#### PIR

- Source page: `Alarm/PIR/API.html`
- Purpose: This API is used for get or set PIR parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/PIR/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Alarm/PIR/Get.html`
- Purpose: This API is used to get parameter for Alarm > PIR.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/PIR/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "page_type":"AlarmConfig"
    }
}
```

#### Range

- Source page: `Alarm/PIR/Range.html`
- Purpose: This API is used to get the parameter range of Alarm > PIR.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/PIR/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "page_type":"AlarmConfig"
    }
}
```

#### Set

- Source page: `Alarm/PIR/Set.html`
- Purpose: This API is used to set parameter for Alarm > PIR .
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/PIR/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "channel_info":
        {
            "CH4":
            {
                "buzzer":"0",
                "alarm_out":[],
                "latch_time":"10",
                "record_enable":true,
                "record_channel":["CH4"],"post_recording":"30",
                "show_message":false,
                "send_email":false,
                "full_screen":false,"ftp_picture_upload":false,"ftp_video_upload":false,"picture_to_cloud":false,"video_to_cloud":false,"http_listening":false,"voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],
                "voice_prompts_select":[0,0],"voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all",
                "chn_index":"CH4"
            },
            "CH18":
            {
                "buzzer":"0",
                "alarm_out":[],
                "latch_time":"10",
                "record_enable":true,
                "record_channel":["CH18"],"post_recording":"30",
                "show_message":false,
                "send_email":false,
                "full_screen":false,"ftp_picture_upload":false,"ftp_video_upload":false,"picture_to_cloud":false,"video_to_cloud":false,"http_listening":false,"voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],
                "voice_prompts_select":[0,0],"voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all"
            }
        },
        "page_type":"AlarmConfig"
    }
}
```

### PTZ Linkage

#### PTZ Linkage

- Source page: `Alarm/PTZ Linkage/API.html`
- Purpose: This API is used to get or set PTK Linkage alarm parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/PTZLinkage/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Alarm/PTZ Linkage/Get.html`
- Purpose: This API is used to get parameter for Alarm > PTZ Linkage.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/PTZLinkage/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Range

- Source page: `Alarm/PTZ Linkage/Range.html`
- Purpose: This API is used to get the parameter range of Alarm > PTZ Linkage.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/PTZLinkage/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Set

- Source page: `Alarm/PTZ Linkage/Set.html`
- Purpose: This API is used to set parameter for Alarm > PTZ Linkage.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/PTZLinkage/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {
            "CH1": {
                "switch": false,
                "all_alarm": {
                    "motion": true,
                    "pir": true,
                    "io": true,
                    "linkage_sod": true,
                    "linkage_cc": true,
                    "linkage_sound": true,
                    "linkage_vt": true,
                    "linkage_fd": true,
                    "linkage_ad": true,
                    "linkage_cd": true,
                    "linkage_qd": true,
                    "linkage_lpd": true,
                    "linkage_rsd": true,
                    "linkage_lpr": true,
                    "linkage_fr": true,
                    "linkage_ai_pid": true,
                    "linkage_ai_lcd": true,
                    "linkage_ai_pdvd": true,
                    "linkage_ai_firedetet": false,
                    "linkage_ai_tempmeas": false,
                    "linkage_intrusion": false,
                    "linkage_region_entrance": false,
                    "linkage_region_exiting": false
                },
                "ptz_info": [
                    {
                        "ptz_switch": false,
                        "ptz_chn": "CH1",
                        "linkage_ptz_point_index": 0
                    },
                    {
                        "ptz_switch": false,
                        "ptz_chn": "CH2",
                        "linkage_ptz_point_index": 0
                    },
                    {
                        "ptz_switch": false,
                        "ptz_chn": "CH3",
                        "linkage_ptz_point_index": 0
                    },
                    {
                        "ptz_switch": false,
                        "ptz_chn": "CH4",
                        "linkage_ptz_point_index": 0
                    }
                ],
                "copy_ch": "digit",
                "chn_index": "CH1",
                "alarm_type": []
            }
        }
    },
    "page_type": "AlarmConfig"
}
```

### Sound Detection

#### Sound Detection

- Source page: `Alarm/Sound Detection/API.html`
- Purpose: This API is used for get or set SoundDetection config parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/SoundDetection/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Alarm/Sound Detection/Get.html`
- Purpose: This API is used to get parameter for Alarm > Sound Detection.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/SoundDetection/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "page_type":"AlarmConfig"
    }
}
```

#### Range

- Source page: `Alarm/Sound Detection/Range.html`
- Purpose: This API is used to get the parameter range of Alarm > Sound Detection .
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/SoundDetection/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "page_type":"ChannelConfig"
    }
}
```

#### Set

- Source page: `Alarm/Sound Detection/Set.html`
- Purpose: This API is used to set parameter for Alarm > Sound Detection.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/SoundDetection/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "channel_info":
        {
            "CH4":
            {
                "buzzer":"0",
                "alarm_out":[],
                "latch_time":"10",
                "record_enable":true,
                "record_channel":["CH4"],"post_recording":"30",
                "show_message":true,
                "send_email":true,
                "full_screen":false,"ftp_picture_upload":false,"ftp_video_upload":false,"picture_to_cloud":false,"http_listening":false,"video_to_cloud":false,"voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],
                "voice_prompts_select":[0,0],"voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all",
                "chn_index":"CH4"
            },
            "CH18":
            {
                "buzzer":"0",
                "alarm_out":[],
                "latch_time":"10",
                "record_enable":true,
                "record_channel":["CH18"],"post_recording":"30",
                "show_message":true,
                "send_email":true,
                "full_screen":false,"ftp_picture_upload":false,"ftp_video_upload":false,"picture_to_cloud":false,"http_listening":false,"video_to_cloud":false,"voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],
                "voice_prompts_select":[0,0],"voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all"
            }
        },
        "page_type":"AlarmConfig"
    }
}
```

### Stationary Object Detection

#### Stationary Object Detection

- Source page: `Alarm/Stationary Object Detection/API.html`
- Purpose: This API is used for get or set SOD config parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/SOD/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Alarm/Stationary Object Detection/Get.html`
- Purpose: This API is used to get parameter for Alarm > Stationary Object Detection.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/SOD/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "page_type":"AlarmConfig"
    }
}
```

#### Range

- Source page: `Alarm/Stationary Object Detection/Range.html`
- Purpose: This API is used to get the parameter range of Alarm > Stationary Object Detection.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/SOD/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "AlarmConfig"}
}
```

#### Set

- Source page: `Alarm/Stationary Object Detection/Set.html`
- Purpose: This API is used to set parameter for Alarm > Stationary Object Detection.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Intelligent/SOD/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "channel_info":
        {
            "CH4":
            {
                "buzzer":"0",
                "alarm_out":[],
                "latch_time":"10",
                "record_enable":true,"http_listening":false,
                "record_channel":["CH4"],"post_recording":"30",
                "show_message":false,
                "send_email":false,
                "full_screen":false,"ftp_picture_upload":false,"ftp_video_upload":false,"picture_to_cloud":false,"video_to_cloud":false,"voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],
                "voice_prompts_select":[0,0],"voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all",
                "chn_index":"CH4"
            },
            "CH18":
            {
                "buzzer":"0",
                "alarm_out":[],
                "latch_time":"10",
                "record_enable":true,"http_listening":false,
                "record_channel":["CH18"],"post_recording":"30",
                "show_message":false,
                "send_email":false,
                "full_screen":false,"ftp_picture_upload":false,"ftp_video_upload":false,"picture_to_cloud":false,"video_to_cloud":false,"voice_prompts_index":[0,0,0,0,0,0,0,0,0,0,0,0],
                "voice_prompts_select":[0,0],"voice_prompts_time":[
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    },
                    {
                        "start_hour":0,
                        "start_minute":0,
                        "start_second":0,
                        "end_hour":23,
                        "end_minute":59,
                        "end_second":59
                    }
                ],
                "copy_ch":"all"
            }
        },
        "page_type":"AlarmConfig"
    }
}
```

### VoiceAlarm

#### Voice Alarm

- Source page: `Alarm/VoiceAlarm/API.html`
- Purpose: This API is used to get or set sound alarm parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/VoiceAlarm/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Delete

- Source page: `Alarm/VoiceAlarm/Delete.html`
- Purpose: This API is used to delete imported audio files.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/VoiceAlarm/Delete
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {
            "CH1": {
                "siren_type": "User-defined2"
            }
        }
    }
}
```

#### Get

- Source page: `Alarm/VoiceAlarm/Get.html`
- Purpose: This API is used to get Alarm > Voice Alarm parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/VoiceAlarm/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Import

- Source page: `Alarm/VoiceAlarm/Import.html`
- Purpose: This API is used to import alert audio files.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/VoiceAlarm/Import
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {
            "CH1": {
                "siren_type": "Alarm1",
                "siren_file_name": "FILE.wav",
                "siren_file_type": ".wav",
                "file_data": "ADSD+ASD.ADASD"
            }
        }
    }
}
```

#### Range

- Source page: `Alarm/VoiceAlarm/Range.html`
- Purpose: This API is used to get Alarm > Voice Alarm parameter range.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/VoiceAlarm/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Alarm/VoiceAlarm/Set.html`
- Purpose: This API is used to set Alarm > Voice Alarm parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/VoiceAlarm/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {
            "CH1": {
                "siren_switch": true,
                "siren_time": 62,
                "siren_value": 62,
                "siren_type": "Alarm1"
            }
        }
    }
}
```

### VoicePrompts

#### Voice Prompts

- Source page: `Alarm/VoicePrompts/API.html`
- Purpose: This API is used to get or set language broadcast configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/VoicePrompts/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Alarm/VoicePrompts/Get.html`
- Purpose: This API is used to get Alarm > Voice Prompts configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/VoicePrompts/Get
```
- Request Body (JSON):
```json
{
    "data": {
        "command": "GetAudioFilesList ",
    }
}
```

#### Range

- Source page: `Alarm/VoicePrompts/Range.html`
- Purpose: This API is used to get Alarm > Voice Prompts configuration parameter range.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/VoicePrompts/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "control_type":"Normal"
    }
}
```

#### Set

- Source page: `Alarm/VoicePrompts/Set.html`
- Purpose: This API is used to set Alarm > Voice Prompts configuration parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/VoicePrompts/Set
```
```http
POST http://000.00.00.000/API/AlarmConfig/VoicePrompts/Set
```
```http
POST http://000.00.00.000/API/AlarmConfig/VoicePrompts/Set
```
```http
POST http://000.00.00.000/API/AlarmConfig/VoicePrompts/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "control_type": "Normal",
        "command": "Remove",
        "download_mode": "mp3",
        "index": 45
    }
}
```
```json
{
    "version": "1.0",
    "data": {
        "fileIndex": 0,
        "fileName": "CC.mp3",
        "chunkSize": 1,
        "chunkIndex": 0,
        "data": "//MoxAAM+F...qqqqqqqqq",
        "control_type": "Normal",
        "command": "Upload",
        "convert_mode": "File",
        "download_mode": "mp3",
        "file_count": 1,
        "packet_index": 0,
        "package_size": 10560,
        "file_name": "CC.mp3",
        "file_data": "//MoxAq...qqqqqqq"
    }
}
```
```json
{
    "version": "1.0",
    "data": {
        "control_type": "Normal",
        "command": "Upload",
        "convert_mode": "NetworkText",
        "download_mode": "mp3",
        "language": "ENGLISH",
        "text": "test",
        "file_name": "name"
    }
}
```
```json
{
    "version": "1.0",
    "data": {
        "control_type": "Normal",
        "command": "Transform",
        "download_mode": "mp3",
        "index": 46
    }
}
```

## Channel

### Channel Configuration / Analog Channel

#### Analog Channel

- Source page: `Channel/Channel Configuration/Analog Channel/API.html`
- Purpose: This API is used to get or set Analog Channel page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/AnalogChannel/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Channel/Channel Configuration/Analog Channel/Get.html`
- Purpose: This API is used to get Channel > Analog Channel page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/AnalogChannel/Get
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"page_type": "ChannelConfig"
	}
}
```

#### Range

- Source page: `Channel/Channel Configuration/Analog Channel/Range.html`
- Purpose: This API is used to get parameter range for Channel > Analog Channel page.
- Endpoint:
```http
POST http://000.00.00.000/ChannelConfig/AnalogChannel/Range
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"page_type": "ChannelConfig"
	}
}
```

#### Set

- Source page: `Channel/Channel Configuration/Analog Channel/Set.html`
- Purpose: This API is used to set Channel > Analog Channel page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/AnalogChannel/Set
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"channel_info": {
			"CH1": {
				"channel_name": "CH1",
				"state": "Enable",
				"switch": true,
				"channel": "CH1"
			},
			"CH2": {
				"channel_name": "CH2",
				"state": "Enable",
				"switch": true,
				"channel": "CH2"
			},
			"CH3": {
				"channel_name": "CH3",
				"state": "Enable",
				"switch": true,
				"channel": "CH3"
			},
			"CH4": {
				"channel_name": "CH4",
				"state": "Enable",
				"switch": true,
				"channel": "CH4"
			},
			"CH5": {
				"channel_name": "CH5",
				"state": "Enable",
				"switch": true,
				"channel": "CH5"
			},
			"CH6": {
				"channel_name": "CH6",
				"state": "Enable",
				"switch": true,
				"channel": "CH6"
			},
			"CH7": {
				"channel_name": "CH7",
				"state": "Enable",
				"switch": true,
				"channel": "CH7"
			},
			"CH8": {
				"channel_name": "CH8",
				"state": "Enable",
				"switch": true,
				"channel": "CH8"
			}
		}
	}
}
```

### Channel Configuration / Broadcast IPC

#### Broadcast IPC

- Source page: `Channel/Channel Configuration/Broadcast IPC/API.html`
- Purpose: This API is used to broadcast search or modify IPC information.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/RemoteDev/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Range

- Source page: `Channel/Channel Configuration/Broadcast IPC/Range.html`
- Purpose: This API is used to get parameter range for Channel > Channel Configuration > Broadcast IPC page.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/RemoteDev/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Search

- Source page: `Channel/Channel Configuration/Broadcast IPC/Search.html`
- Purpose: This API is used to broadcast search IPC information.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/RemoteDev/Search
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Channel/Channel Configuration/Broadcast IPC/Set.html`
- Purpose: This API is used to broadcast set IPC information.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/RemoteDev/Set
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"device_info": [
			{
				"tips_ensure_ip_not_use": true,
				"network_mode": "Dhcp",
				"hide_network_mode": false,
				"ip_address": "172.16.8.5",
				"subnet_mask": "255.255.252.000",
				"gateway": "172.016.008.001",
				"dns1": "000.000.000.000",
				"dns2": "000.000.000.000",
				"port": 80,
				"channel_num": 1,
				"protocol": "Private",
				"manufacturer": " ",
				"activesign": 1,
				"fmulti_devid": "WjNFZWZRWnMwTW1EM1E1VU1ZV1NrYjFGdWJTYU1sL29Lc2VXbjgyMjNaYz0=",
				"device_type": "NC591XB",
				"device_type_flag": "0",
				"mac_address": "00-23-63-A2-91-B0",
				"software_version": "V40.45.8.2.4_230705",
				"ismodify_username": true,
				"ismodify_dhcp": true,
				"ismodify_ip": true,
				"ismodify_port": true,
				"password_empty": true,
				"version_flag": 0,
				"No": 1,
				"web_port": 80,
				"old_ip_address": "172.16.8.5",
				"username": ""
			}
		]
	}
}
```

### Channel Configuration / Channel Configuration

#### Channel Configuration

- Source page: `Channel/Channel Configuration/Channel Configuration/API.html`
- Purpose: This API is used to get or set Channel Configuration page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ChannelConfig/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Channel/Channel Configuration/Channel Configuration/Get.html`
- Purpose: This API is used to get Channel > Channel Configuration page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ChannelConfig/Get
```
- Request Body (JSON):
```json
To be added
```

#### Range

- Source page: `Channel/Channel Configuration/Channel Configuration/Range.html`
- Purpose: This API is used to get parameter range for Channel  > Channel Configuration page.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ChannelConfig/Range
```
- Request Body (JSON):
```json
To be added
```

#### Set

- Source page: `Channel/Channel Configuration/Channel Configuration/Set.html`
- Purpose: This API is used to set Channel > Channel Configuration page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ChannelConfig/Set
```
- Request Body (JSON):
```json
To be added
```

### Channel Configuration / IPChannel

#### IPChannel

- Source page: `Channel/Channel Configuration/IPChannel/API.html`
- Purpose: This API is used to get or set IPChannel page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/IPChannel/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### AutoAddIPC

- Source page: `Channel/Channel Configuration/IPChannel/AutoAddIPC.html`
- Purpose: This API is used to automatically broadcast add IPC.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/AutoAddIPC/Set
```
- Request Body (JSON):
```json
To be added
```

#### Get

- Source page: `Channel/Channel Configuration/IPChannel/Get.html`
- Purpose: This API is used to get Channel > IPChannel page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/IPChannel/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `Channel/Channel Configuration/IPChannel/Range.html`
- Purpose: This API is used to get parameter range for Channel > IPChannel page.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/IPChannel/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Channel/Channel Configuration/IPChannel/Set.html`
- Purpose: This API is used to set Channel > IPChannel page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/IPChannel/Set
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"channel_info": {
			"CH1": {
				"state": "Online",
				"ip_address": "172.16.11.5",
				"main_url": "",
				"sub_url": "",
				"subnet_mask": "255.255.252.000",
				"gateway": "172.016.008.001",
				"port": 80,
				"channel_num": 1,
				"channel_index": 0,
				"protocol": "Private",
				"connect_method": "General",
				"username": "admin",
				"password_empty": false,
				"manufacturer": "",
				"device_type": "SSC30KQ+SC2315",
				"mac_address": "00-23-63-94-AA-08",
				"software_version": "V31.35.8.2.4_230710",
				"network_mode": "Dhcp",
				"forward_port": 65001
			}
		},
		"operation_type": "EditIPCParam"
	}
}
```

### Channel Configuration / Protocol Manage

#### Protocol Manage

- Source page: `Channel/Channel Configuration/Protocol Manage/API.html`
- Purpose: This API is used to get or set Protocol Manage page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ProtocolManage/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Channel/Channel Configuration/Protocol Manage/Get.html`
- Purpose: This API is used to get Channel > Protocol Manage page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ProtocolManage/Get
```
- Request Body (JSON):
```json
To be added
```

#### Range

- Source page: `Channel/Channel Configuration/Protocol Manage/Range.html`
- Purpose: This API is used to get parameter range for Channel  > Protocol Manage page.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ProtocolManage/Range
```
- Request Body (JSON):
```json
To be added
```

#### Set

- Source page: `Channel/Channel Configuration/Protocol Manage/Set.html`
- Purpose: This API is used to set Channel > Protocol Manage page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ProtocolManage/Set
```
- Request Body (JSON):
```json
To be added
```

### Channel Configuration / Wireless Camera

#### Wireless Camera

- Source page: `Channel/Channel Configuration/Wireless Camera/API.html`
- Purpose: This API is used to get or set Wireless Camera page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/WirelessCamera/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Channel/Channel Configuration/Wireless Camera/Get.html`
- Purpose: This API is used to get Channel > Wireless Camera page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/WirelessCamera/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `Channel/Channel Configuration/Wireless Camera/Range.html`
- Purpose: This API is used to get parameter range for Channel  > Wireless Camera page.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/WirelessCamera/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Channel/Channel Configuration/Wireless Camera/Set.html`
- Purpose: This API is used to set Channel > Wireless Camera page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/WirelessCamera/Set
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"channel_info": {
			"CH1": {
				"channel_name": "Channel1 1111111",
				"software_version": "V33.21.5.2_220429_50V",
				"chn_index": "CH1",
				"page": "chn_wireChn"
			},
			"CH2": {
				"channel_name": "Channel 2",
				"software_version": "V25.11.5.2_220407"
			},
			"CH3": {
				"channel_name": "Channel 3",
				"software_version": "V21.15.5.2_221207"
			},
			"CH4": {
				"channel_name": "Channel 4",
				"software_version": "V33.21.5.2_220520_50V"
			},
			"CH5": {
				"channel_name": "Channel 5",
				"software_version": "V33.21.5.2_220429_50V"
			},
			"CH6": {
				"channel_name": "Channel 6",
				"software_version": "V41.11.0.1_230706_W-0706"
			}
		},
		"page_type": "ChannelConfig"
	}
}
```

### Image Control

#### Image Control

- Source page: `Channel/Image Control/API.html`
- Purpose: This API is used to get or set Image Control page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ImageControl/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Default

- Source page: `Channel/Image Control/Default.html`
- Purpose: This API is used to get Channel > Image Control page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ImageControl/Default
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"channel": [
			"CH14"
		]
	}
}
```

#### Get

- Source page: `Channel/Image Control/Get.html`
- Purpose: This API is used to get Channel > Image Control page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ImageControl/Get
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {}
}
```

#### Range

- Source page: `Channel/Image Control/Range.html`
- Purpose: This API is used to get parameter range for Channel > Image Control page.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ImageControl/Range
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {}
}
```

#### Set

- Source page: `Channel/Image Control/Set.html`
- Purpose: This API is used to set Channel > Image Control page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ImageControl/Set
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"channel_info": {
			"CH3": {
				"support_default": true,
				"ir_cut_mode": "ImageMode",
				"image_sensitivity": 1,
				"ir_led": "Auto",
				"mirror_mode": "Close",
				"corridor_mode": "Close",
				"angle_rotation": "0",
				"Daylight": {
					"back_light": "Close",
					"denoising": "Auto",
					"denoising_level": 128,
					"gain": 64,
					"white_balance": "Auto",
					"red_tuning": 44,
					"green_tuning": 27,
					"blue_tuning": 54,
					"exposure_mode": "Auto",
					"shutter_limit": "1/8"
				},
				"wdr_hide_ai_area": false,
				"Night": {
					"back_light": "Close",
					"denoising": "Auto",
					"denoising_level": 128,
					"gain": 64,
					"white_balance": "Auto",
					"red_tuning": 44,
					"green_tuning": 27,
					"blue_tuning": 54,
					"exposure_mode": "Auto",
					"shutter_limit": "1/8"
				},
				"camera_param_mode": "Daylight",
				"chn_index": "CH3",
				"page": "chn_imgCtrl"
			}
		}
	}
}
```

### OSD

#### OSD

- Source page: `Channel/OSD/API.html`
- Purpose: This API is used to get or set Video Cover page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/OSD/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Channel/OSD/Get.html`
- Purpose: This API is used to get Channel > OSD page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/OSD/Get
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {}
}
```

#### Range

- Source page: `Channel/OSD/Range.html`
- Purpose: This API is used to get parameter range for Channel  > OSD page.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/OSD/Range
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {}
}
```

#### Set

- Source page: `Channel/OSD/Set.html`
- Purpose: This API is used to set Channel > OSD page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/OSD/Set
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"channel_info": {
			"CH1": {
				"status": "Online",
				"channel_enable": true,
				"name": {
					"show": true,
					"text": "Camera",
					"pos": {
						"x": 290,
						"y": 0
					}
				},
				"datetime": {
					"show": true,
					"date_format": "YYYY-MM-DD",
					"time_format": 24,
					"pos": {
						"x": 390,
						"y": 0
					}
				},
				"alarm": {
					"show": true,
					"text": "In: - Out: -",
					"pos": {
						"x": 0,
						"y": 50
					}
				},
				"refresh_rate": "60Hz",
				"covert": false,
				"osd_invert": false,
				"chn_index": "CH1",
				"page": "chn_osd"
			},
			"CH5": {
				"status": "Online",
				"channel_enable": true,
				"name": {
					"show": true,
					"text": "Camera",
					"pos": {
						"x": 290,
						"y": 0
					}
				},
				"datetime": {
					"show": true,
					"date_format": "MM/DD/YYYY",
					"time_format": 24,
					"pos": {
						"x": 390,
						"y": 0
					}
				},
				"covert": false
			},
			"CH14": {
				"status": "Online",
				"channel_enable": true,
				"name": {
					"show": true,
					"text": "Camera",
					"pos": {
						"x": 290,
						"y": 0
					}
				},
				"datetime": {
					"show": true,
					"date_format": "YYYY-MM-DD",
					"time_format": 24,
					"pos": {
						"x": 390,
						"y": 0
					}
				},
				"alarm": {
					"show": true,
					"text": "In: - Out: -",
					"pos": {
						"x": 0,
						"y": 50
					}
				},
				"refresh_rate": "60Hz",
				"covert": false
			},
			"CH15": {
				"status": "Online",
				"channel_enable": true,
				"name": {
					"show": true,
					"text": "Camera",
					"pos": {
						"x": 290,
						"y": 0
					}
				},
				"datetime": {
					"show": true,
					"date_format": "YYYY-MM-DD",
					"time_format": 24,
					"pos": {
						"x": 390,
						"y": 0
					}
				},
				"alarm": {
					"show": true,
					"text": "In: - Out: -",
					"pos": {
						"x": 0,
						"y": 50
					}
				},
				"refresh_rate": "60Hz",
				"covert": false,
				"osd_invert": false
			}
		}
	}
}
```

### POE Power

#### POE Power

- Source page: `Channel/POE Power/API.html`
- Purpose: This API is used to get POE Power page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/PoePower/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Channel/POE Power/Get.html`
- Purpose: This API is used to get Channel > POE Power page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/PoePower/Get
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {}
}
```

### PTZ

#### PTZ

- Source page: `Channel/PTZ/API.html`
- Purpose: This API is used to get or set PTZ page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/PTZ/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Channel/PTZ/Get.html`
- Purpose: This API is used to get Channel > PTZ page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/PTZ/Get
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {}
}
```

#### Range

- Source page: `Channel/PTZ/Range.html`
- Purpose: This API is used to get parameter range for Channel  > PTZ page.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/PTZ/Range
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {}
}
```

#### Set

- Source page: `Channel/PTZ/Set.html`
- Purpose: This API is used to set Channel > PTZ page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/PTZ/Set
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"channel_info": {
			"CH1": {
				"signal_type": "Analog",
				"protocol": "COAX1",
				"baudrate": "9600",
				"databit": "8",
				"stopbit": "1",
				"parity": "None",
				"address": 1,
				"copy_ch": "analog",
				"chn_index": "CH1"
			},
			"CH2": {
				"signal_type": "Analog",
				"protocol": "COAX1",
				"baudrate": "9600",
				"databit": "8",
				"stopbit": "1",
				"parity": "None",
				"address": 2,
				"copy_ch": "analog"
			},
			"CH3": {
				"signal_type": "Analog",
				"protocol": "COAX1",
				"baudrate": "9600",
				"databit": "8",
				"stopbit": "1",
				"parity": "None",
				"address": 3,
				"copy_ch": "analog"
			},
			"CH4": {
				"signal_type": "Analog",
				"protocol": "COAX1",
				"baudrate": "9600",
				"databit": "8",
				"stopbit": "1",
				"parity": "None",
				"address": 4,
				"copy_ch": "analog"
			},
			"CH5": {
				"signal_type": "Analog",
				"protocol": "COAX1",
				"baudrate": "9600",
				"databit": "8",
				"stopbit": "1",
				"parity": "None",
				"address": 5,
				"copy_ch": "analog"
			},
			"CH6": {
				"signal_type": "Analog",
				"protocol": "COAX1",
				"baudrate": "9600",
				"databit": "8",
				"stopbit": "1",
				"parity": "None",
				"address": 6,
				"copy_ch": "analog"
			},
			"CH7": {
				"signal_type": "Analog",
				"protocol": "COAX1",
				"baudrate": "9600",
				"databit": "8",
				"stopbit": "1",
				"parity": "None",
				"address": 7,
				"copy_ch": "analog"
			},
			"CH8": {
				"signal_type": "Analog",
				"protocol": "COAX1",
				"baudrate": "9600",
				"databit": "8",
				"stopbit": "1",
				"parity": "None",
				"address": 8,
				"copy_ch": "analog"
			}
		},
		"page_type": "AlarmConfig"
	}
}
```

### Remote Pair

#### Remote Pair (Only for Wireless)

- Source page: `Channel/Remote Pair/API.html`
- Purpose: This API is used to set up remote pairing.
- Endpoint:
```http
POST http://000.00.00.000/API/Login/ChannelPairing/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Range

- Source page: `Channel/Remote Pair/Range.html`
- Purpose: This API is used to get a range of remote pairing parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/Login/ChannelPairing/Range
```
- Request Body (JSON):
```json
To be added.
```

#### Set

- Source page: `Channel/Remote Pair/Set.html`
- Purpose: This API is used to set up remote pairing.
- Endpoint:
```http
POST http://000.00.00.000/API/Login/ChannelPairing/Set
```
- Request Body (JSON):
```json
To be added
```

### ROI

#### ROI

- Source page: `Channel/ROI/API.html`
- Purpose: This API is used to get or set ROI page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ROI/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Channel/ROI/Get.html`
- Purpose: This API is used to get Channel > ROI page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ROI/Get
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {}
}
```

#### Range

- Source page: `Channel/ROI/Range.html`
- Purpose: This API is used to get parameter range for Channel  > ROI page.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ROI/Range
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {}
}
```

#### Set

- Source page: `Channel/ROI/Set.html`
- Purpose: This API is used to set Channel > ROI page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ROI/Set
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"channel_info": {
			"CH1": {
				"main_stream_info": {
					"region_id_1": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						},
						"regionID_index": "region_id_1",
						"chn_index": "CH1",
						"page": "chn_roi",
						"stream_index": "main_stream_info"
					},
					"region_id_2": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_3": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_4": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_5": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_6": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_7": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_8": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					}
				},
				"sub_stream_info": {
					"region_id_1": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_2": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_3": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_4": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_5": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_6": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_7": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_8": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					}
				},
				"mobile_stream_info": {
					"region_id_1": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_2": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_3": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_4": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_5": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_6": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_7": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_8": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					}
				}
			},
			"CH3": {
				"main_stream_info": {
					"region_id_1": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"main_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_2": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"main_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_3": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"main_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_4": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"main_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_5": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"main_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_6": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"main_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_7": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"main_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_8": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"main_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					}
				},
				"sub_stream_info": {
					"region_id_1": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"sub_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_2": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"sub_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_3": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"sub_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_4": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"sub_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_5": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"sub_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_6": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"sub_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_7": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"sub_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_8": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"sub_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					}
				},
				"mobile_stream_info": {
					"region_id_1": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"mobile_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_2": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"mobile_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_3": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"mobile_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_4": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"mobile_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_5": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"mobile_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_6": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"mobile_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_7": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"mobile_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					},
					"region_id_8": {
						"roi_switch": false,
						"roi_level": "Lowest",
						"mobile_non_roi_fps": "1",
						"rect": {
							"left": 0,
							"top": 0,
							"width": 0,
							"height": 0
						}
					}
				}
			}
		}
	}
}
```

### Scheduled Tasks

#### API

- Source page: `Channel/Scheduled Tasks/API.html`
- Purpose: This API is used to get or set for the Scheduled Tasks page
- Endpoint:
```http
POST http://000.00.00.000/API/Schedules/PtzTasks/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Channel/Scheduled Tasks/Get.html`
- Purpose: This API is used to get Channel > Scheduled Tasks Page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/Schedules/PtzTasks/Get
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {}
}
```

#### Range

- Source page: `Channel/Scheduled Tasks/Range.html`
- Purpose: This API is used to get Channel > Scheduled Tasks parameter scale。
- Endpoint:
```http
POST http://000.00.00.000/API/Schedules/PtzTasks/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Channel/Scheduled Tasks/Set.html`
- Purpose: This API is used to Set Channel > Scheduled Tasks Page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/Schedules/PtzTasks/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"channel_info": {"CH1": {
        "schedule_tasks_enable": true,
        "belt_times_use": 0,
        "schedule": [
            {
                "schedule_type": "Close",
                "week": [
                    {
                        "day": "Sun",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Mon",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Tue",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Wed",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Thu",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Fri",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Sat",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    }
                ]
            },
            {
                "schedule_type": "Line Scan",
                "week": [
                    {
                        "day": "Sun",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Mon",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Tue",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Wed",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Thu",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Fri",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Sat",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    }
                ]
            },
            {
                "schedule_type": "Tour",
                "week": [
                    {
                        "day": "Sun",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Mon",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Tue",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Wed",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Thu",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Fri",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Sat",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    }
                ]
            },
            {
                "schedule_type": "Pattern Scan",
                "week": [
                    {
                        "day": "Sun",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Mon",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Tue",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Wed",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Thu",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Fri",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Sat",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    }
                ]
            },
            {
                "schedule_type": "Preset",
                "week": [
                    {
                        "day": "Sun",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Mon",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Tue",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Wed",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Thu",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Fri",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    },
                    {
                        "day": "Sat",
                        "time": [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0
                        ]
                    }
                ]
            }
        ],
        "tasks_recovery_times": 5,
        "chn_index": "CH1",
        "scheduleType": "Close",
        "scheduleTypeNum": 0,
        "ptzSchedule": {
            "data": [
                [
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ]
                ],
                [
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ]
                ],
                [
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ]
                ],
                [
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ]
                ],
                [
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ],
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0
                    ]
                ]
            ],
            "ptzData": [
                [
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1"
                ],
                [
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1"
                ],
                [
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1"
                ],
                [
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1"
                ],
                [
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1"
                ],
                [
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1"
                ],
                [
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1",
                    "-1"
                ]
            ],
            "colors": [
                "#666",
                "#B9E2FE",
                "#66eeff",
                "#004d99",
                "#32a0e1"
            ],
            "schType": "schedule_ptz",
            "aiColorsLen": 1,
            "words": [
                "Close",
                "Line Scan",
                "Tour",
                "Pattern Scan",
                "Preset"
            ],
            "titlewords": [
                "Close",
                "Line Scan",
                "Tour",
                "Pattern Scan",
                "Preset"
            ],
            "selcolor": 0,
            "selnumArr": [
                [0],
                [0],
                [
                    1,
                    2,
                    3,
                    4
                ],
                [
                    1,
                    2,
                    3,
                    4
                ],
                [
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8
                ]
            ],
            "selnum": 0,
            "cells": {
                "width": "25px",
                "height": "20px"
            },
            "weeks": [
                "SUN",
                "MON",
                "TUE",
                "WED",
                "THU",
                "FRI",
                "SAT"
            ],
            "radio": 3,
            "defaultSelType": {"default": 0},
            "rows": 7,
            "cols": 48,
            "radioWidth": "20px"
        }
    }}}
}
```

### Video Color

#### Video Color

- Source page: `Channel/Video Color/API.html`
- Purpose: This API is used to get or set Video Color page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/Color/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Default

- Source page: `Channel/Video Color/Default.html`
- Purpose: This API is used to get Channel > Video Color page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/Color/Default
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"channel": [
			"CH1"
		]
	}
}
```

#### Get

- Source page: `Channel/Video Color/Get.html`
- Purpose: This API is used to get Channel > Video Color page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/Color/Get
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {}
}
```

#### Range

- Source page: `Channel/Video Color/Range.html`
- Purpose: This API is used to get parameter range for Channel  > Video Color page.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/Color/Range
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {}
}
```

#### Set

- Source page: `Channel/Video Color/Set.html`
- Purpose: This API is used to set Channel > Video Color page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/Color/Set
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"channel_info": {
			"CH1": {
				"hue": 128,
				"bright": 128,
				"contrast": 128,
				"saturation": 128,
				"sharpness": 192,
				"support_default": true,
				"last_hue": 50,
				"last_bright": 50,
				"last_contrast": 50,
				"last_saturation": 50,
				"last_sharpness": 50,
				"SunRise_time": "00:00",
				"SunSet_time": "00:00",
				"palette": "White Hot"
			}
		}
	}
}
```

### Video Cover

#### Video Cover

- Source page: `Channel/Video Cover/API.html`
- Purpose: This API is used to get or set Video Cover page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/VideoCover/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Channel/Video Cover/Get.html`
- Purpose: This API is used to get Channel > Video Cover page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/VideoCover/Get
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {}
}
```

#### Range

- Source page: `Channel/Video Cover/Range.html`
- Purpose: This API is used to get parameter range for Channel  > Video Cover page.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/VideoCover/Range
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {}
}
```

#### Set

- Source page: `Channel/Video Cover/Set.html`
- Purpose: This API is used to set Channel > Video Color page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/VideoCover/Set
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"channel_info": {
			"CH1": {
				"hue": 128,
				"bright": 128,
				"contrast": 128,
				"saturation": 128,
				"sharpness": 192,
				"support_default": true,
				"last_hue": 50,
				"last_bright": 50,
				"last_contrast": 50,
				"last_saturation": 50,
				"last_sharpness": 50,
				"SunRise_time": "00:00",
				"SunSet_time": "00:00",
				"palette": "White Hot"
			}
		}
	}
}
```

### Video Crop

#### Video Crop

- Source page: `Channel/Video Crop/API.html`
- Purpose: This API is used to get or set Video Crop page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/VideoCrop/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Channel/Video Crop/Get.html`
- Purpose: This API is used to get Channel > Video Crop page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/VideoCrop/Get
```
- Request Body (JSON):
```json
To be added
```

#### Range

- Source page: `Channel/Video Crop/Range.html`
- Purpose: This API is used to get parameter range for Channel  > Video Crop page.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/VideoCrop/Range
```
- Request Body (JSON):
```json
To be added
```

#### Set

- Source page: `Channel/Video Crop/Set.html`
- Purpose: This API is used to set Channel > Video Crop page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/VideoCrop/Set
```
- Request Body (JSON):
```json
To be added
```

## ConsumerInfo

### Root

#### Get

- Source page: `ConsumerInfo/Get.html`
- Purpose: This API is used to get ConsumerInfo parameter。
- Endpoint:
```http
HTTP/1.1 200 OK
Content-Type: application/json
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Set

- Source page: `ConsumerInfo/Set.html`
- Purpose: This API is used for setup ConsumerInfo parameter。
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ImageControl/Set
```
- Request Body (JSON):
```json
{
 "data":{
        "domain_name":"xxxx",
        "customer_id":"00",
        "cloud_id":"xxxx"
    }
}
```

## Event

### Event_check&Event_push

#### event check

- Source page: `Event/Event_check&Event_push/API.html`
- Purpose: Get alarms and push alarms: Get&Push
- Endpoint: Not explicitly documented in a request sample on this page.
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Event/Event_check&Event_push/Get&Push.html`
- Purpose: This API is used to get parameter for Event > event check page.
- Endpoint:
```http
POST http://000.00.00.000/API/Event/Check
HTTP/1.1
```
- Request Body (JSON):
```json
{
    version": "1.0",
    "data": {
        "plus_eventchk": "eventAiPushPic",
        "ext_data": {
                        "subscribe_type": [{"event": ["all"]}]
                        },
        "reader_id": 1,
        "sequence": 9595,
        "lap_number": null
    }
}
```

### Http_listening

#### Http listening

- Source page: `Event/Http_listening/API.html`
- Purpose: It is used to get or set the ALL ALARM config parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/EventPush/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Event/Http_listening/Get.html`
- Purpose: This API is used to get parameter for Event > Http listening page.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/EventPush/Get
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Range

- Source page: `Event/Http_listening/Range.html`
- Purpose: This API is used to get parameter range for Event > Http listening page.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/EventPush/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Event/Http_listening/Set.html`
- Purpose: This API is used to set parameter for Event > Http listening page.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/EventPush/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"params": {
        "name": "",
        "table": {
            "username": "",
            "password_empty": true,
            "addr": "",
            "port": 123,
            "url": "API/AlarmEvent/EventPush",
            "enable": false,
            "method": "POST",
            "keep_alive_interval": "0",
            "push_way": "HTTP",
            "udp_method": "Broadcast",
            "udp_addr": "255.255.255.255",
            "udp_port": 5000
        }
    }}
}
```

### Http_listening_Push related description / get

#### Http listening Push related description

- Source page: `Event/Http_listening_Push related description/get/API.html`
- Purpose: This API pushes alarms by Get.
- Endpoint:
```http
Get /API/AlarmEvent/EventPush?EventType=xx&EventTime=xx&EventAction=xx&MACAddress=xx
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Event/Http_listening_Push related description/get/Get.html`
- Purpose: This API is used to get parameter for Event > Http listening Push related description page.
- Endpoint:
```http
GET http://000.00.00.000/API/AlarmEvent/EventPush?EventType=VideoMotion&EventTime=2023-7-13 7:18:49&EventAction=start&ChannelName=senvi&MACAddress=00-23-63-69-23-6D
Host: 172.16.8.138:123
Accept: */*
Content-Type: application/json;charset=UTF-8
```
- Request Body (JSON): No JSON request body sample was documented on this page.

### Http_listening_Push related description / keeplive

#### Http listening Push related description

- Source page: `Event/Http_listening_Push related description/keeplive/API.html`
- Purpose: This API device sends a liveliness request to the client server.
- Endpoint:
```http
POST http://000.00.00.000/API/HttpListening/{action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### KeepLive

- Source page: `Event/Http_listening_Push related description/keeplive/KeepLive.html`
- Purpose: This API is used to get parameter for Event > Http listening Push related description page.
- Endpoint:
```http
POST http://000.00.00.000/API/HttpListening/KeepLive
Host: 172.16.8.238:123
Accept: */*
Content-Type: application/json;charset=UTF-8
Content-Length: 30
```
- Request Body (JSON): No JSON request body sample was documented on this page.

### Http_listening_Push related description / post

#### Http listening Push related description

- Source page: `Event/Http_listening_Push related description/post/API.html`
- Purpose: This API pushes alarms by POST.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmEvent/EventPush{action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### POST

- Source page: `Event/Http_listening_Push related description/post/POST.html`
- Purpose: This API is used to push Event > Http listening Push related description alarm event requests.
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmEvent/EventPush
Host: 172.16.8.138:123
Accept: */*
Content-Type: application/json;charset=UTF-8
Content-Length: 231
```
- Request Body (JSON): No JSON request body sample was documented on this page.

### Subscribe to api Design

#### Subscribe to api Design

- Source page: `Event/Subscribe to api Design/Subscribe to api Design.html`
- Endpoint:
```http
POST http://000.00.00.000/API/AlarmConfig/Combination/Get
```
- Request Body (JSON): No JSON request body sample was documented on this page.

## ExtendedFunctionality

### AI Mutex Relation

#### AIMutexRelation

- Source page: `ExtendedFunctionality/AI Mutex Relation/API.html`
- Purpose: This API is used for get  AIMutexRelation  parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/AIMutexRelation/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `ExtendedFunctionality/AI Mutex Relation/GET.html`
- Purpose: This API is used to get parameter for Extended Functionality > AIMutexRelation .
- Endpoint:
```http
POST http://000.00.00.000/API/AIMutexRelation/Get
HTTP/1.1
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

### IPCVoice Prompt

#### IPCVoice Prompt

- Source page: `ExtendedFunctionality/IPCVoice Prompt/API.html`
- Purpose: It is used to get or set the IPCVoice Prompt config parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/Extended/IPCVoicePrompts/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `ExtendedFunctionality/IPCVoice Prompt/Get.html`
- Purpose: This API is used to get parameter for Extended Functionality > IPCVoice Prompt page.
- Endpoint:
```http
POST http://000.00.00.000/API/Extended/IPCVoicePrompts/Get
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Set

- Source page: `ExtendedFunctionality/IPCVoice Prompt/Set.html`
- Endpoint:
```http
POST http://000.00.00.000/API/Extended/IPCVoicePrompts/Set
```
- Request Body (JSON): No JSON request body sample was documented on this page.

### Mutex Relation

#### Mutex Relation

- Source page: `ExtendedFunctionality/Mutex Relation/API.html`
- Purpose: This API is used to get MutexRelation parameter.
- Endpoint:
```http
POST http://000.00.00.000/API/MutexRelation/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `ExtendedFunctionality/Mutex Relation/Get.html`
- Purpose: This API is used to get parameter for  Extended Functionality > Mutex Relation page.
- Endpoint:
```http
POST http://000.00.00.000/API/MutexRelation/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

## Function

### ANR

#### ANR

- Source page: `Function/ANR/API.html`
- Purpose: This API is used to obtain client Macs.
- Endpoint:
```http
POST http://000.00.00.000/API/ANRConfig/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### GetANRTimeInfo

- Source page: `Function/ANR/GetANRTimeInfo.html`
- Purpose: This API is used to get parameter for Function > ANR page.
- Endpoint:
```http
POST http://000.00.00.000/API/ANRConfig/GetANRTimeInfo
```
- Request Body (JSON):
```json
{
"data": {
        " device_flag ": "88-DF-58-18-4F-47 "
    }
}
```

#### GetClientMac

- Source page: `Function/ANR/GetClientMac.html`
- Purpose: This API is used to set parameter for Function > ANR page.
- Endpoint:
```http
POST http://000.00.00.000/API/ANRConfig/GetClientMac
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### SetANRInfo

- Source page: `Function/ANR/SetANRInfo.html`
- Purpose: This API is used to set parameter for Function > ANR page.
- Endpoint:
```http
POST http://000.00.00.000/API/ANRConfig/SetANRInfo
```
- Request Body (JSON): No JSON request body sample was documented on this page.

### ETR

#### ETR

- Source page: `Function/ETR/API.html`
- Purpose: This API is used to obtain client Mac
- Endpoint:
```http
POST http://000.00.00.000/API/Function/ETR/ {Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Set

- Source page: `Function/ETR/Set.html`
- Purpose: This API is used to set parameter for Function > ETR page.
- Endpoint:
```http
POST http://000.00.00.000/API/StreamConfig/EventStreamState/Set
```
- Request Body (JSON): No JSON request body sample was documented on this page.

### Request I Frame

#### Request I Frame

- Source page: `Function/Request I Frame/API.html`
- Purpose: This API is used for get or setRequest I Frame page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/RequestIDR/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Range

- Source page: `Function/Request I Frame/Range.html`
- Purpose: This API is used to get parameter range for Function >  Request I Frame  page.
- Endpoint:
```http
POST/API/RequestIDR HTTP/1.1
```
- Request Body (JSON):
```json
{
	“data”: {
    "chn_no": 0,
    “stream_type”:” Mainstream”
}
}
```

### Snapshot

#### Snapshot

- Source page: `Function/Snapshot/API.html`
- Purpose: This API is used for get the information of Snapshot
- Endpoint:
```http
POST http://000.00.00.000/API/Snapshot/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Function/Snapshot/Get.html`
- Purpose: This API is used to get parameter for Function > Snapshot page.
- Endpoint:
```http
POST http://000.00.00.000/API/Snapshot/Get
HTTP/1.1
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel":"CH1",
        "snapshot_resolution":"1280 x 720",
        "reset_session_timeout":false
    }
}
```

#### Range

- Source page: `Function/Snapshot/Range.html`
- Purpose: This API is used to get parameter range for Function > Snapshot page.
- Endpoint:
```http
POST http://000.00.00.000/API/Snapshot/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data":{"reset_session_timeout":false}
}
```

## Login

### Account Rules

#### Account Rules

- Source page: `Login/Account Rules/API.html`
- Endpoint:
```http
POST http://000.00.00.000/API/AccountRules/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Login/Account Rules/Get.html`
- Purpose: Get user rule restrictions.
- Endpoint:
```http
POST http://000.00.00.000/API/AccountRules/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
    }
}
```

### DevicePage

#### DevicePage

- Source page: `Login/DevicePage/API.html`
- Endpoint:
```http
POST http://000.00.00.000/API/Login/DevicePage/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Login/DevicePage/Get.html`
- Purpose: This API is used for get Remote Setting page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/Login/DevicePage/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Level 1 Menu

- Source page: `Login/DevicePage/Pages.html`
- Endpoint: Not explicitly documented in a request sample on this page.
- Request Body (JSON): No JSON request body sample was documented on this page.

### FirstLogin

#### FirstLogin

- Source page: `Login/FirstLogin/API.html`
- Purpose: This API includes the API for setting the password for the first login of the device.
- Endpoint:
```http
POST http://000.00.00.000/API/FirstLogin/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

### FirstLogin / Password

#### Password

- Source page: `Login/FirstLogin/Password/API.html`
- Purpose: This API includes the API for setting the password for the first login of the device.
- Endpoint:
```http
POST http://000.00.00.000/API/FirstLogin/Password/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Set

- Source page: `Login/FirstLogin/Password/Set.html`
- Purpose: This API is used to set the password for the first login of the device.
- Endpoint:
```http
POST http://000.00.00.000/API/FirstLogin/Password/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "base_enc_password": {
            "seq": 0,
            "peer_key": "0z3+fzVXn/msq6ZagsHDY57sI29XtP3qIL+gVOW4hJH8=",
            "cipher": "075RisUMqoS9110GpXIoJhlJJQORLeWpmU12SZpcSFkDMLfIj"
        },
        "activation_pwd": {
            "seq": 0,
            "peer_key": "09BuUR966wl41vQIcS2WwAQRh3mATOABaq3TYSDfheh4=",
            "cipher": "0Cn8dz0BTQ0uM4BGHVRwuHXzeurPj2BeFKB8kOb2dkVmKr959sw=="
        }
    }
}
```

### Login

#### Login

- Source page: `Login/Login/API.html`
- Purpose: This API includes APIs such as heartbeat, getting device information before and after login, and getting channel information.
Client login and subsequent process reference:
- Endpoint:
```http
POST http://000.00.00.000/API/Login/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

### Login / ChannelInfo

#### ChannelInfo

- Source page: `Login/Login/ChannelInfo/API.html`
- Purpose: This API includes APIs such as obtaining channel information after login.
- Endpoint:
```http
POST http://000.00.00.000/API/Login/ChannelInfo/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Login/Login/ChannelInfo/Get.html`
- Purpose: This API is used to get channel information
- Endpoint:
```http
POST http://000.00.00.000/API/Login/ChannelInfo/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

### Login / DeviceInfo

#### DeviceInfo

- Source page: `Login/Login/DeviceInfo/API.html`
- Purpose: This API is used to get device information after login.
- Endpoint:
```http
POST http://000.00.00.000/API/Login/DeviceInfo/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Login/Login/DeviceInfo/Get.html`
- Purpose: Get device information.
- Endpoint:
```http
POST http://000.00.00.000/API/Login/DeviceInfo/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

### Login

#### Heartbeat

- Source page: `Login/Login/Heartbeat.html`
- Purpose: This API is used to send heartbeat, and send a heartbeat request every 30s after login to ensure that the heartbeat does not expire after timeout.
- Endpoint:
```http
POST http://000.00.00.000/API/Login/Heartbeat
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "keep_alive": true
    }
}
```

#### Range

- Source page: `Login/Login/Range.html`
- Purpose: This API is used to get device information before login.
- Endpoint:
```http
POST http://000.00.00.000/API/Login/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

### PreviewChannel

#### PreviewChannel

- Source page: `Login/PreviewChannel/API.html`
- Purpose: This API includes Get PTZ Information, Control PTZ, Get Light Siren Information, Control Light Siren, Get DualTalk Information, Control DualTalk, Get Manual Alarm Information, Control Manual Alarm.
- Endpoint:
```http
POST http://000.00.00.000/API/PreviewChannel/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

### PreviewChannel / DualTalk

#### DualTalk

- Source page: `Login/PreviewChannel/DualTalk/API.html`
- Purpose: This API includes getting and setting two-way intercom information.
- Endpoint:
```http
POST http://000.00.00.000/API/PreviewChannel/DualTalk/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Login/PreviewChannel/DualTalk/Get.html`
- Purpose: This API is used to obtain two-way intercom information.
- Endpoint:
```http
POST http://000.00.00.000/API/PreviewChannel/DualTalk/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data":{
        "channel":"IP_CH4",
        "command_flag":false,
    }
}
```

#### Set

- Source page: `Login/PreviewChannel/DualTalk/Set.html`
- Purpose: This API is used to control two-way intercom.
- Endpoint:
```http
POST http://000.00.00.000/API/PreviewChannel/DualTalk/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data":{
        "channel": "CH1",
        "action": 1
    }
}
```

### PreviewChannel / Floodlight2AudioAlarm

#### Floodlight2AudioAlarm

- Source page: `Login/PreviewChannel/Floodlight2AudioAlarm/API.html`
- Purpose: This API includes getting and setting flood light to audio alarm parameter.
- Endpoint:
```http
POST http://000.00.00.000/API/PreviewChannel/Floodlight2AudioAlarm/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Login/PreviewChannel/Floodlight2AudioAlarm/Get.html`
- Purpose: This API is used to get light siren information.
- Endpoint:
```http
POST http://000.00.00.000/API/PreviewChannel/Floodlight2AudioAlarm/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data":{
        "channel":"IP_CH4",
        "command_flag":false,
    }
}
```

#### Set

- Source page: `Login/PreviewChannel/Floodlight2AudioAlarm/Set.html`
- Purpose: This API contains parameters for setting light and sound sirens.
- Endpoint:
```http
POST http://000.00.00.000/API/PreviewChannel/Floodlight2AudioAlarm/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data":{
        "channel":"CH8",
        "redBlueLight_switch":true,
        "audioAlarm_switch":false,
        "audioAlarm_value":5,
        "audioAlarm_value_range":
        {
            "type":"int32",
            "min":1,
            "max":10
        },
        "audioAlarm_value_adjustable":true,
        "operation_type":"RedBlueLight"
    }
}
```

### PreviewChannel / ManualAlarm

#### ManualAlarm

- Source page: `Login/PreviewChannel/ManualAlarm/API.html`
- Purpose: This API contains parameters for getting and setting lights and sounds for sirens.
- Endpoint:
```http
POST http://000.00.00.000/API/PreviewChannel/ManualAlarm/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Login/PreviewChannel/ManualAlarm/Get.html`
- Purpose: This API contains parameters for setting light and sound sirens.
- Endpoint:
```http
POST http://000.00.00.000/API/PreviewChannel/ManualAlarm/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data":{
    }
}
```

#### Set

- Source page: `Login/PreviewChannel/ManualAlarm/Set.html`
- Purpose: This API is used to control manual alarms.
- Endpoint:
```http
POST http://000.00.00.000/API/PreviewChannel/ManualAlarm/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data":{
        "Local->1": true,
        "Local->2": true,
        "IP_CH1->1": true
    }
}
```

### PreviewChannel / PTZ

#### PTZ

- Source page: `Login/PreviewChannel/PTZ/API.html`
- Purpose: This API is used for getting control PTZ and PTZ status information or controlling PTZ.
- Endpoint:
```http
POST http://000.00.00.000/API/PreviewChannel/PTZ/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Control

- Source page: `Login/PreviewChannel/PTZ/Control.html`
- Purpose: This API is used to control PTZ.
- Endpoint:
```http
POST http://000.00.00.000/API/PreviewChannel/PTZ/Control
```
```http
POST http://000.00.00.000/API/PreviewChannel/PTZ/Control
```
```http
POST http://000.00.00.000/API/PreviewChannel/PTZ/Control
```
- Request Body (JSON):
```json
{
  "version": "1.0",
  "data": {
    "channel": "CH2",
    "cmd": "Ptz_Btn_Refresh",
    "speed": 50,
    "zoom_step": 5,
    "zoom_slider": 1,
    "focus_step": 1,
    "focus_slider": 180
  }
}
```
```json
{
  "version": "1.0",
  "data": {
    "channel": "CH2",
    "cmd": "Ptz_Cmd_FocusAdd",
    "state": "Stop",
    "speed": 50,
    "zoom_step": 5,
    "zoom_slider": 2,
    "focus_step": 1,
    "focus_slider": 126
  }
}
```
```json
{
  "version": "1.0",
  "data": {
    "channel": "CH2",
    "cmd": "Ptz_Btn_AutoFocus",
    "speed": 50,
    "zoom_step": 5,
    "zoom_slider": 2,
    "focus_step": 1,
    "focus_slider": 127
  }
}
```

### PreviewChannel / PTZ / Control

#### Progress

- Source page: `Login/PreviewChannel/PTZ/Control/Progress.html`
- Purpose: This API is used to get PTZ status.
- Endpoint:
```http
POST http://000.00.00.000/API/PreviewChannel/PTZ/Control/Progress
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data":{
        "channel": "CH1"
    }
}
```

### PreviewChannel / PTZ

#### Get

- Source page: `Login/PreviewChannel/PTZ/Get.html`
- Purpose: This API is used to get PTZ control information.
- Endpoint:
```http
POST http://000.00.00.000/API/PreviewChannel/PTZ/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data":{
        "channel": "CH1",
        "disable_ManualHumanTrace": false,
        "current_cruise_mode": "Mode_Default_Cruise",
        "zoom_step": 5,
        "focus_step": 5
    }
}
```

### RecoverPassword

#### RecoverPassword

- Source page: `Login/RecoverPassword/API.html`
- Purpose: This API includes APIs such as getting password recovery configuration parameters, getting password recovery page parameters, setting passwords, password recovery question verification parameters, verifying password recovery question answers, exporting certificates, and sending verification codes by email.
- Endpoint:
```http
POST http://000.00.00.000/API/RecoverPassword/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

### RecoverPassword / Authorization

#### Authorization

- Source page: `Login/RecoverPassword/Authorization/API.html`
- Purpose: This API is used for getting or setting the recover password authorization parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/RecoverPassword/Authorization/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Login/RecoverPassword/Authorization/Get.html`
- Purpose: This API is used to get parameter for Login > RecoverPassword > Authorization page.
- Endpoint:
```http
POST http://000.00.00.000/API/RecoverPassword/Authorization/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `Login/RecoverPassword/Authorization/Range.html`
- Purpose: This API is used to obtain the verification parameter range for password recovery.
- Endpoint:
```http
POST http://000.00.00.000/API/RecoverPassword/Authorization/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Login/RecoverPassword/Authorization/Set.html`
- Purpose: This API is used to set the verification question for recovering the password.
- Endpoint:
```http
POST http://000.00.00.000/API/RecoverPassword/Authorization/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "answer_flag": true,
        "questions": [
            1,
            2,
            3
        ],
        "email_flag": false,
        "certificate_flag": true,
        "super_pwd_flag": true,
        "enc_answers": {
            "seq": 0,
            "peer_key": "0ehkbgxtTrULIODyzNMAEISzRq86LqwzGdLMKWB5g+T8=",
            "cipher": [
                "0R6rrZLwivuja3Lg3yMl6TWY4wppC0eM/ECgV3sw=",
                "0RKrrZLwivuja3Lg3yEE5XXywwIoMzMM27Q3IAkw=",
                "0RarrZLwivuja3Lg3yDkHrXU3PoXJOCMxue6DScw="
            ]
        }
    }
}
```

### RecoverPassword / Certificate

#### Certificate

- Source page: `Login/RecoverPassword/Certificate/API.html`
- Purpose: This API is used for exporting certificate API.
- Endpoint:
```http
POST http://000.00.00.000/API/RecoverPassword/Certificate/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Export

- Source page: `Login/RecoverPassword/Certificate/Export.html`
- Purpose: This API is used to export certificate API.
- Endpoint:
```http
POST http://000.00.00.000/API/RecoverPassword/Certificate/Export
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

### RecoverPassword / Email

#### Email

- Source page: `Login/RecoverPassword/Email/API.html`
- Purpose: This API is used for sending verification code to email.
- Endpoint:
```http
POST http://000.00.00.000/API/RecoverPassword/Email/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Send

- Source page: `Login/RecoverPassword/Email/Send.html`
- Purpose: This API is used to send verification code to email.
- Endpoint:
```http
POST http://000.00.00.000/API/RecoverPassword/Email/Send
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

### RecoverPassword

#### Get

- Source page: `Login/RecoverPassword/Get.html`
- Purpose: This API is used to obtain configuration parameters for retrieving passwords.
- Endpoint:
```http
POST http://000.00.00.000/API/RecoverPassword/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
    }
}
```

#### Range

- Source page: `Login/RecoverPassword/Range.html`
- Purpose: This API is used to get the range of RecoverPassword config parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/RecoverPassword/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {

    }
}
```

#### Set

- Source page: `Login/RecoverPassword/Set.html`
- Endpoint:
```http
POST http://000.00.00.000/API/RecoverPassword/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "answer_flag": true,
        "email_flag": true,
        "certificate_flag": true,
        "super_pwd_flag": true,
        "questions": [5, 4, 3],
        "answers": ["111", "222", "333"],
        "email": "123456@qq.com"
    }
}
```

### Request pubkey or randbyte

#### Request pubkey or randbyte

- Source page: `Login/Request pubkey or randbyte/API.html`
- Purpose: This API is used for requesting user password transmission encryption key and PBKDF2_SHA256 random number and user password transmission encryption key for logging in when the device is inactive.
- Endpoint:
```http
POST http://000.00.00.000/API/{Action}/TransKey/Get
```
- Request Body (JSON): No JSON request body sample was documented on this page.

### Request pubkey or randbyte / demo

#### pbkdf2

- Source page: `Login/Request pubkey or randbyte/demo/pbkdf2.html`
- Endpoint: Not explicitly documented in a request sample on this page.
- Request Body (JSON): No JSON request body sample was documented on this page.

#### x25519

- Source page: `Login/Request pubkey or randbyte/demo/x25519.html`
- Endpoint: Not explicitly documented in a request sample on this page.
- Request Body (JSON): No JSON request body sample was documented on this page.

### Request pubkey or randbyte

#### Table 1

- Source page: `Login/Request pubkey or randbyte/EncryptObjectTable.html`
- Endpoint: Not explicitly documented in a request sample on this page.
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Login

- Source page: `Login/Request pubkey or randbyte/Login.html`
- Purpose: This API is used to transmit the user password to encrypted key, Used before login when device isnot activated.
- Endpoint:
```http
POST http://000.00.00.000/API/Login/TransKey/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "type": [
            "base_salt",
            "base_x_public"
        ]
    }
}
```

#### Maintenance

- Source page: `Login/Request pubkey or randbyte/Maintenance.html`
- Purpose: This API is used for requesting user password transmission encryption key and PBKDF2_SHA256 random number and user password transmission encryption key for logging in when the device is inactive.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/TransKey/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "type": [
            "base_salt",
            "base_x_public"
        ]
    }
}
```

### Web

#### Web

- Source page: `Login/Web/API.html`
- Purpose: This API is used for login and logout API.
- Endpoint:
```http
POST http://000.00.00.000/API/Web/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Login

- Source page: `Login/Web/Login.html`
- Purpose: This API is used for login functionality. The client uses digest authentication to login; when the login is successful, in the http header, two fields are returned, Set-cookie and X-csrftoken;such as:
- Endpoint:
```http
POST http://000.00.00.000/API/Web/Login
```
- Validation note: Backend-verified. Your backend sends exactly this body with Digest Auth.
- Request Body (JSON):
```json
{
    "data": {}
}
```

#### Logout

- Source page: `Login/Web/Logout.html`
- Purpose: This API is used for logout.
- Endpoint:
```http
POST http://000.00.00.000/API/Web/Logout
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
    }
}
```

## Maintenance

### Auto Reboot

#### Auto Reboot

- Source page: `Maintenance/Auto Reboot/API.html`
- Purpose: This API contains get and set to get auto restart page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/AutoReboot/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Maintenance/Auto Reboot/Get.html`
- Purpose: This API is used to get auto restart page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/AutoReboot/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `Maintenance/Auto Reboot/Range.html`
- Purpose: This API is used to get the auto restart page parameter range.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/AutoReboot/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Maintenance/Auto Reboot/Set.html`
- Purpose: This API is used to set auto restart page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/AutoReboot/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "auto_reboot":false,
        "period_mode":"EveryWeek",
        "time":"00:00",
        "week":"Sun"
    }
}
```

### DefoggingFan

#### DefoggingFan

- Source page: `Maintenance/DefoggingFan/API.html`
- Purpose: This API is used for getting fan switch information and set fan switch.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/DefoggingFan/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Maintenance/DefoggingFan/Get.html`
- Purpose: This API is used to get fan switch information.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/DefoggingFan/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `Maintenance/DefoggingFan/Range.html`
- Purpose: This API is used to get fan switch information range.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/DefoggingFan/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Maintenance/DefoggingFan/Set.html`
- Purpose: This API is used to set fan switch.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/DefoggingFan/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "defogging_fan": true
    }
}
```

### DeveloperMode

#### DeveloperMode

- Source page: `Maintenance/DeveloperMode/API.html`
- Purpose: This API is used to get and set developer page parameters, clear and export log files.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/DeveloperMode/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Clear

- Source page: `Maintenance/DeveloperMode/Clear.html`
- Purpose: This API is used to clear configuration file which in disk.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/DeveloperMode/Clear
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "base_secondary_authentication": {
            "seq": 1,
            "cipher": "CowFtnYJVzraDlE+OngLJfGaS7FXFjy6zXkILkSzB3A="
        },
        "delete_type": "NVR_Ipc"
    }
}
```

#### Download

- Source page: `Maintenance/DeveloperMode/Download.html`
- Purpose: This API is used to download configuration file.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/DeveloperMode/Download
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Maintenance/DeveloperMode/Get.html`
- Purpose: This API is used to get the developer mode page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/DeveloperMode/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `Maintenance/DeveloperMode/Range.html`
- Purpose: This API is used to get the parameter range of the developer mode page.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/DeveloperMode/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Maintenance/DeveloperMode/Set.html`
- Purpose: This API is used to set the Developer Mode configuration.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/DeveloperMode/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{
        "ssh_switch":false,
        "export_disk_switch":"Shut Off"
    }
}
```

#### Token

- Source page: `Maintenance/DeveloperMode/Token.html`
- Purpose: This API is used to get Token.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/DeveloperMode/Token
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "base_secondary_authentication": {
            "seq": 3,
            "cipher": "egLU4qef8erLd7RAfoYZ6q8pxe3EFYruonZhuceK4Pk="
        },
        "channel": [
            "CH1",
            "CH2",
            "CH3",
            "CH4",
            "CH5",
            "CH6",
            "CH7",
            "CH8",
            "CH9",
            "CH10",
            "CH11",
            "CH12",
            "CH13",
            "CH14",
            "CH15",
            "CH16"
        ],
        "export_days": "all",
        "download_type": "NVR_Ipc"
    }
}
```

### DeviceReboot

#### DeviceReboot

- Source page: `Maintenance/DeviceReboot/API.html`
- Purpose: This API is used for rebooting device API.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/DeviceReboot/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Set

- Source page: `Maintenance/DeviceReboot/Set.html`
- Purpose: This API is used to reboot device.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/DeviceReboot/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "cipher" : "0bjEvTI4Lr8jsytAHx8bSXPNk7cuvIFYGCQjIUH2S/sVPnNQO",
        "seq": 0
    }
}
```

### DeviceShutdown

#### DeviceShutdown

- Source page: `Maintenance/DeviceShutdown/API.html`
- Purpose: This API is used for device shutdown.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/DeviceShutdown/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Set

- Source page: `Maintenance/DeviceShutdown/Set.html`
- Purpose: This API is used to device shutdown.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/DeveloperMode/Clear
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "base_secondary_authentication":{
            "seq":2,
            "cipher":"FWRsfpB05p/NfdTleipoBR1d06/dZA2xO8cDJiF4CYM="
        }
    }
}
```

### FtpUpgrade

#### FtpUpgrade

- Source page: `Maintenance/FtpUpgrade/API.html`
- Purpose: This API contains APIs for obtaining online upgrade parameters, setting update parameters, checking for updates, performing upgrades, and obtaining upgrade progress.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/FtpUpgrade/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Check

- Source page: `Maintenance/FtpUpgrade/Check.html`
- Purpose: This API is used to check for upgrade.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/FtpUpgrade/Check
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Get

- Source page: `Maintenance/FtpUpgrade/Get.html`
- Purpose: This API is used to obtain online upgrade parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/FtpUpgrade/Get
```
```http
POST http://000.00.00.000/API/Maintenance/FtpUpgrade/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```
```json
{
    "version": "1.0",
    "data": {
        "url_key": {
            "type": "base_x_public",
            "peer_key": "0uegOWQD2zcee4hnx4hFDN1bmul9ETG2uzX9ndpfo5nk=",
            "seq": 0
        }
    }
}
```

#### Progress

- Source page: `Maintenance/FtpUpgrade/Progress.html`
- Purpose: This API is used to get upgrade progress.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/FtpUpgrade/Progress
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `Maintenance/FtpUpgrade/Range.html`
- Purpose: This API is used to obtain the online upgrade parameter range.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/FtpUpgrade/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Maintenance/FtpUpgrade/Set.html`
- Purpose: This API is used to set upgrade configuration.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/FtpUpgrade/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "ftp_addr":"",
        "ftp_port":21,
        "username":"admin",
        "user_pwd_empty":true,
        "ftp_path":"ftp://192.168.1.100:23/device/upgradePackage",
        "check_for_updates":true,
        "online_upgrade":true,
        "Upgrade_button":false,
        "base_enc_password":
        {
            "seq":0,
            "peer_key":"0rD95mGwiZznl34bejOzwEOK+PZZZnOeLoKzw794TmSM=","cipher":"05XviOTKBMiUlzS5IL8P9CWATcxELsON78EdFHbpQ9qSA1umq"
        }
    }
}
```

#### Upgrade

- Source page: `Maintenance/FtpUpgrade/Upgrade.html`
- Purpose: This API is used for online upgrades.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/FtpUpgrade/Upgrade
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{
    }
}
```

### Import_Export Parameter

#### Import/Export Parameter

- Source page: `Maintenance/Import_Export Parameter/API.html`
- Purpose: This API is used for Importing and exporting configuration files.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/ParamManagement/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Maintenance/Import_Export Parameter/Get.html`
- Purpose: This API is used to export configuration files.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/ParamManagement/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "base_secondary_authentication":
        {
            "seq":1,
            "cipher":"EvATuCptX+3MBm+BWmKDpHBem0u4YmH4Z7Mf0Jk2gig="
        }
    }
}
```

#### Set

- Source page: `Maintenance/Import_Export Parameter/Set.html`
- Purpose: This API is used to import and exporting configuration files.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/ParamManagement/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "param":"kB9be+toauFV21fneBk45GHN018JxEmKIhq0l5CspWmS......HO/mHhE79z3w8XkDD+mzgvxNCMr40/Dq",
        "base_secondary_authentication":
        {
            "seq":2,
            "cipher":"GJF4i4o7nYahUGO16n8sqrMbGhx+NH7B6ehhxRVjOOs="
        }
    }
}
```

### IPCMaintenance / FtpIpcUpgrade

#### FtpIpcUpgrade

- Source page: `Maintenance/IPCMaintenance/FtpIpcUpgrade/API.html`
- Purpose: This API is used for getting IPC ftp update parameters,setting IPC ftp update parameters、Check for IPC upgrade, IPC ftp upgrade and get IPC update progress.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/FtpIpcUpgrade/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Check

- Source page: `Maintenance/IPCMaintenance/FtpIpcUpgrade/Check.html`
- Purpose: This API is used to check for IPC upgrade.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/FtpIpcUpgrade/Check
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{
        "check_chns":[
            "CH8",
            "CH15",
            "CH16"
        ]
    }
}
```

#### Get

- Source page: `Maintenance/IPCMaintenance/FtpIpcUpgrade/Get.html`
- Purpose: This API is used to get IPC ftp update parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/FtpIpcUpgrade/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Progress

- Source page: `Maintenance/IPCMaintenance/FtpIpcUpgrade/Progress.html`
- Purpose: This API is used to get IPC update progress.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/FtpUpgrade/Progress
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "upgrade_chns":[
            "CH8",
            "CH15",
            "CH16"
        ]
    }
}
```

#### Range

- Source page: `Maintenance/IPCMaintenance/FtpIpcUpgrade/Range.html`
- Purpose: This API is used to get range of IPC ftp update parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/FtpIpcUpgrade/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Maintenance/IPCMaintenance/FtpIpcUpgrade/Set.html`
- Purpose: This API is used to set IPC ftp update parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/FtpIpcUpgrade/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{
        "online_upgrade":true,
        "ftp_auto_upgrade":false,
        "check_for_updates":false,
        "channel_info":{
            "CH3":{
                "reason":"Not support"
            },
            "CH7":{
                "reason":"Not support"
            },
            "CH8":{
                "sup_ftp_auto_upgrade":true,
                "upgrade_result":"cannot_upgrade",
                "ftp_ipc_new_ver":false
            },
            "CH10":{
                "reason":"Not support"
            },
            "CH11":{
                "sup_ftp_auto_upgrade":false
            },
            "CH14":{
                "reason":"Not support"
            },
            "CH15":{
                "sup_ftp_auto_upgrade":true,
                "upgrade_result":"cannot_upgrade",
                "ftp_ipc_new_ver":false
            },
            "CH16":{
                "sup_ftp_auto_upgrade":true,
                "upgrade_result":"",
                "ftp_ipc_new_ver":false
            }
        }
    }
}
```

#### Upgrade

- Source page: `Maintenance/IPCMaintenance/FtpIpcUpgrade/Upgrade.html`
- Purpose: This API is used to IPC ftp upgrade.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/FtpIpcUpgrade/Upgrade
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{
        "upgrade_chns":[
            "CH8",
            "CH15",
            "CH16"
        ]
    }
}
```

### IPCMaintenance / IPCParamManagement

#### IPCParamManagement

- Source page: `Maintenance/IPCMaintenance/IPCParamManagement/API.html`
- Purpose: This API is used for getting IPC parameters for System > IPC Camera Maintain > Param Management page and import or export IPC configuration files.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/IPCParamManagement/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Export

- Source page: `Maintenance/IPCMaintenance/IPCParamManagement/Export.html`
- Purpose: This API is used to export IPC configuration files.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/IPCParamManagement/Export
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "base_secondary_authentication":
        {
            "seq":2,
            "cipher":"7RUcFX+UNep/faAvjE9k+ZcEwSl7WKIy2AS9YzDmRE8="
        },
        "channel_info":
        {
            "CH16":
            {
                "ImportExportSwitch":true
            }
        }
    }
}
```

#### Get

- Source page: `Maintenance/IPCMaintenance/IPCParamManagement/Get.html`
- Purpose: This API is used to get IPC parameters for System > IPC Camera Maintain > Param Management page.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/IPCParamManagement/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
    }
}
```

#### Import

- Source page: `Maintenance/IPCMaintenance/IPCParamManagement/Import.html`
- Purpose: This API is used to NVR import IPC configuration files.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/IPCParamManagement/Import
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "base_secondary_authentication":
        {
            "seq":2,
            "cipher":"7RUcFX+UNep/faAvjE9k+ZcEwSl7WKIy2AS9YzDmRE8="
        },
        "channel_info":
        {
            "CH16":
            {
                "ImportExportSwitch":true,
                "param": "qhEAAPkVAAAEAAAAORkAAElwY0V4cG9ydFBhcmFtAAAAAAAAAAAAAAAAAAAAAAAAL7s2H6TeV41deejHERf/HLkNAu+C6PAx0k1YU7HNduNJUENOVDk4NTI4X003NjhNAAAAAAAAAAAIZgQA/SMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACrAyBimRDV6zq3jtt83K2UfrIOQJfgvUTQIJvpIWuVTNH1TemcUVkibFQypQXEKlqxQAxTGULr48FS4aKLn0+0RQVDllsXEX4K9zwk4nMc+TCxgJgNXbHXHL6JvjAJPuE10CLbLV2XlZuL0ydGzwuGmgfdofw2tv1j3yr5Yj1QJG+k/7cIdZ34SYPn66oCPwwbqBw5EG6b5mOBoFowv80peWMUOQXDsHDYmVv7pQ976GF7GwIOtt4kj3Te3fWrYDggutytHaUm2/59whxESXjw31RlcjGFhSiLtkPjI1FZo7vSSoX/Kc4FyKxISn91vO9pbTZuAFCFJJTv78tCgzu+HOZjVYmqGPH7AEFQ45D8rxNNELoR62mxkJFmUPNCQ7D94+UL8M++Z8QrUVps78vU9yqbZfUft1MPnR+1LdK1ec6aNyxJFiH1N7WZDH/ywGszVEnhftepdeMm0vH0626d3Uh5qF+rhS7aY9ZCjn7CxsUPwi/6Ql5pdVeLKDFYYps7jzxc/x72k57hD66dkhG8KF0iEUlp2RXjTwk0hxjrD5hQ4nqjvL7QWmSTF8eh8APevTu1K8HTElHAXKaG9pOqZw5vssGZsuamfyaNLHPoZiMk9EEugRlMn94UBp9zUCZVRHfgOfLRdp0R9kX87zMRpqCOX45uNSAgFBFIdI4r9y3RrJ7UDVWdaFWb/kegsJpz1KTkCZKp49O5AyiqMk4lo63fT8YAuAIM/SyPVE2wuiiN//n64cVF2AlCvZ5xqUyPbwM1Otq1VhkvkShotoqyeAHhdsZOxUhcjNcpU5IcELEIoZg3y90JzkRdSV7CI/F7UKBSH/HQDKNbJ+OisEG0DFpeGmEuc5hQ5wWLETQrcyOHjEa37aE+BptHZ6grFxQ+O96tnems6MMBBYSXlQ2ZsfgE6/g9SfhJ7+k1eddQPRSEY8jSyqpcjgxENt8VXJKpsxQT44GHLGW1X30pF48jA+zsVTum6Z10ouxq0KVMwCY1sD6EXbmoaSiXk6TUg9dN9GRv7X41xSklL+Tza3xgN3oGt/NSQK16zFY+WZwSoLgCWRwt6l5wI6N9I3xUQg6HFur+HV11QNH5obKKHLkT68BmFFyCU8Bi2V5sIBf8QH7Qeht8YguhkNNKX53Q77kKTZ7XTP1ceAH3yA3TT+1xWCI5RQAdLIhvcmerP8ILRJI//SgeCo/BjxXlh36T2Spf/UAzqrOBkQL4WrHz9NEYfXsTvODr8VvYC+xHkzZqt2uz+lqCksdj3Di8I8Qp34Hcm9etCodQgotFaECCkFyYml8tZB19aPLr2f43zGFoqYMoUTpadtRl42eKIqtZi5l0XwL1gDpHdTFmfHxsyDsmWEev5ODXhCXbkUld5TQxGJfuYwXt3tuLFiAGUVb+avGuR3EAsvrEn+9ixkDtxG4diIPRp6zYlz0AlNgn9UqQp/B+kYURXsZxbJL+gbUUlKAsEVV8mby6yVRvMsbC3pWOEHsPzIV5A9rN0lbw2MG9eDD3k4nP1SSbqq11pFaSsdxa+xQSlFS0on5JR/LhRG570SDQfvYOTFyV1qnv0spc3ei+OHj3NiueLUsGoa4I/zPpkW/JVgh8uIy+sIVqcfljfnhvbaCQRXw+NB/MRBrQvAkuWOeT31S1+GWHlYHvRVgw02TU8ZD73NZPO+nvmJ2aDT2FeguVBv+0SnbZx6YUS+RRlTBM8iQjh3r/T/36VzdqErz6SvVZk7HAG9kzsvWfe9WuLKgqRmIfZvcbiiCBTMEL3mQhyhmyBmPJDkk8zFjkILREVvszi3AVOmm0ObVTGzrBTXJldSb/tibonqA210IBKSWol+F/nvmKVPYryxpZfO4i8oC1eYFCA9W+wsTfAwP6xcIKwtaLZDYfejZaW+Gu/vhuZsNhYrIYo9oasWGwKY1KFPoIqTCLPiZiZtEkJEJCe043RKp4BlVZlcHIH/XG1XhyBmiMa1ElTZPcVMVVevHk2tOggV329WmKk1I0wf2wIY5vPOEH5BDA9ILNACU59kHeqJJtU9srg5WYWDtpRPPtcxm6Ea+UIOQhMMOTfc0bzQPh/BuI2W/FbmoZnXt72AjFTuxOzQhCy3LDd+Ey6qQVUkQ4kpITCHEawxFqeZrakK8ZTEyUSdB2lyRlHegSreiSk6Sh4aok2Uv/XJKv6val8Gu6QXZzydmfHKu22RvYXWl5elZh0CtCpF16LM1+3SIc/9taVayxMR4T56cBIhxaLjQDhyOFVpWUgCxAOzE0odaQdXh1OJOKbIIAZ3WK/Is4hT202m0XopY13qtOLuZaQVIPKFo+ct3Qp6xXbj6Mu53fCSDkXtNUXXt1yGxRzNB8Es2AbtVxG3o9/TYIKsLFaRhdkYY2sdNcY+15AiknasgcrPLWKgrxJsTRqMFAzg3k/o+HvONjBWqA9GJZJjnJgzS9XeGsKDPBqwVWGhSajDrnBZoYqO6h1ScBWXN7KamDl3WOUvdEPtttIjgP8OZxoLsugn7WpfpI+5PPEAwueGN5QsmZvBoj2gIoxlRsxLkh7pPiDNEKgDSR6rK9pK40MY8RZa+ie8Si1SC54BhoxL51+k6LPIkn/EaQNu7f57T2WFTxQsTRxFjOuDmPakpvk3uamny6KM/t5HW3jFGvdImLQc3z7jz9X9NSIgINbDsla/fhxrdFP0a53yvVF/CTkU8kOOxWe5wBakZR9A5Xkoco3IxRPQ/RjTIEhdbrbEY24OP9NC0stBtcXxZc0HA9VHv+GN+2I4kImrs31xIVgitzr/Znuciyv+lYK1dGE1OXQgPnjxq6W68n6BOe1i4eqvz/Pe/YduxCS3WfUwD/i4wLbDluLnXGZG0DQA7QwHdMTReBhjZIm7Uf/YrmA447oBcBf3Oecf5Lhyg/zsPMxVRikOPVqo7RVXzV9FB00NFJV6/fgE8pBCSOM+1eiB8KO8x7eZchz6Dnk+CIyoNV5nE5mS8jwz/zU4/gD7kHciE45U3ODm6fj3LlM+BQg4xBvKqrxgbMlTdyrmrL8y5dyc6RU0eXCKQlxKH7rt04D6HMwn7t16ZtVdGNfsr2jhscEP0vKAUB+VYGwvH8O3Rp7fo6UlKxUzjyGH67G5t3zrOzX+QB5aWp/xivrdcRB6p7o/DqkQZWTbew+Tm7XAp8zhSKdm/rT9V9wPOF7Z30lAJCefii76BFjQGNorPzUiu/pF/AISWT+0td3FqKxmvfosggSJv+HknbwOYsMiRidpQB+arzeABOLqAm+cElREUuE+/aShNdkKv50EexfU5H9nEA9P6qbmj8PKeXFkR7++H1huxqikTGdD3foUHo7blVphTHKLSVX1HNy9f5FBOslZQg6zQ/79cF5eK1sDr/Eu7mAJF3lc35H5cV4yc0GP7Zpb9xJcThNfu+9StCmFsZiv6ZsnjG/5g9SJbmFVZIx0FdmBaTimVaxsGEvS8p+n04/y8+cp67K6L/hFZXf8i5DAHtugzMhS8dL70sqTdf4UB94x4zPv28cUDBhCYI4lzdJN0mX5mCfj3E3DOybGO4gv4TT/G6uXIEEkiGEN1tvXmlXqTBGTcSiLUkjSkBjCkj6iG+HB37HqDdWcgIDZNQ2yvwXO9DDPJig77vu1/PolbHIaKx51vrYfNZkMWXrAl+r8wLSu+ztmL6GvN5YMcbUMwdRMV75oQB1GAEN+fpccXcMTz8SH7hZOet70EyGX7FUhogbtsEcO7D4xXQ/X74MpkIto8LOIRryQgVWIQ+Hw4bLASLFQC3U22iabYpMHzm2Vk7ECFFjhdEmiWZrpsZYfvZvPQ1Pmhvd1cMLUyU5qNgbUm1Hr+zwiqez/o6n2EDpYwzFgU2k8vRDHjE+ktjY0xNGpyIaFZXzObvZV349Mo6H3Cb66TZKVV2bYALme3RHmsxpkVGH3c5RISDOm8NA6XdtIUzCjxBwpN+EHrqwVRNBEzdVoZyC4jbYMQHbzpSOrDkZPG4NCcJNghCiucAxMO74o8N+d0rm67+js3FHeVX+6VijoCguZH8Wh/8ltu58/5gexfRpPfhG2YlxzxXETMdmiCS/az8R/Z7HqTZ3Cn7nbi0H4xmVp9L4gJWGNBntNfXe7BoqPZ2BwvFKC/9IR29buQ0DkFtgGnVi4z/uuzdG5yqFJW5EF3hZxtz+hBt97B/QWPPsqnWfBQGkbnAwueRuG9RNBudZvTtgz1q1Qtulfo6z9KDYjvHXsf2Xbi3SSCgbaNmHAMA9e31NzPZ5ReDVVn/Frp7So0n6/VHIRLJO7c6SIn2wF61/xCgMtC3BAL25GnVNfFwl6oI21/xa8tFYLkDLlJU0RgSIH1XQJgekSTMQpac9jw4mhbo3qsTKBRsVig4QyBX1bmJRxJeS5c+A+goR1+QhGo7R0aZ2QL9rTR39SYREMbSm3nlqZ8K3hM/sXFIOkePh35Dc/Sr4EUk07NiHeNofXy1poujskX52VUA4ewtCPSYVZSfi96qHG3sEI3XOTs4EpI0xZtAJEAQRE3mMpsWgy3MUWTIvvqyiq4SDv6jGv7EAHDpxHSNnPmHjld3dEedDsePF994nqWCO6wG/r0NJFZXB06j9H9JMm83IrsukrXSoSoF+7waBwUN5w79ttZ6ehVJDkOQOYi4oEKJ5ENGisInoMQQ/TVx7xvteGYsOdkJUtQchyi85DMGcj0lx3WjysxrX46qME83hU9kSvjMTvEThfdf68hxQV26ZdaXvE4SGdMFIMPeRI3qOMpt65zlSmy+GG5mIPrKmwGn0MOfBm/bs/tlCKBkbUL4G+arMviBXC+9DQJa28F8Subq2uTR8MwQu2W1WkHUQRhUF64yzw6Wbk05OR3TAVIWn5R2XEt1FRooF6TofnEPmfL7ycvabm8Fn7ZacEvnzUk7Arn1GuEKIe7BS/oed9uHxFr4BM15ai7b0r3ezCk+Q2LOOfJp8KjSBb5ndtEIXVTXbzCce+EhwYdBsVl5c2K4qNbxDZerV4Z8V1P1xTIcHACMAfY3PIZjUDnqG8nG3q+FoQttmkDjjsdHfRc6M1VQ3l8ep75r8jvp06CELCBiR6PTeUNVDpECNyyXopJs62pYaO3Ez/R5OVDPSSIyLEIpTs9GBK8CQqRMRZytAncqf7b1ipcozxvK6QEeMnIgYRRHRClMprSDOAk+rjmp7/9J2fefnY3M2/YDFSvJnzEmrtLsbgL6AnLtc+wuB8tjtdldI4cl23Qms+vIiDra7idF2rTejNKxVOyhHIMiSROxuXXyGxETFFdxrZ7nI2bWrOqzvLf9M59yqw1RapPeG+s9PyRmyAuafbU6/t3wvCzLMpriwKh3IkAxOlewq/+Vb/KyPrjswB9LKcpOyPtogXyzWBT2MJi9S6fQ2rN/wtw+duTROI2Wdv3bO/iZdII/JsfGkekrm2YDZPFpwQzJdKPROwgaV/s0VXcg2dgYewv6G/aAS0LErcKfG+cb8mJw34gt24+GACC3ppueWmATcTlpqxtY6S+c+cm38mFPL2ThmeFtx6ONFSEeYsjxeocAR0K+F6DAEy6gCHdFdz51BmhYn7dmU0zo00KrNaVrC56L967BIQQlq6uR097i1XRlnnWB/GVIDuMU0dSx5tUPuw4ULWx/zonb0Im/LbrYxkk3RJ/JikXA8vmH2/rQQkf5Ui/1pHgcelPn2JZynNs8lc94ZAR1SkQfnfFZTkDugPekwasEdjc0BfUFdjevLBEd5upSZWZrGEBc9KFTheQLxqE87MKP/8G5wWm6U7UjPM9pCxTa9YMYSCbn7+S0P++jVsBf0bSXXkLYdE+u8WMPEuMKUxjUvWMizlXHxPC9cjIVZv1l46tL+v6FGURZPbMSr0YG/tW3jluKeIzPNxA+SnAgn/t/Y6TDhzRK3FC4daYs2lD/pG4zykmFhAsWmiwo5v4YAOgyZ/FNwNx71WhhNyiRABrkHSGVil8bsVZOBwnEXgbWYnS+ombXI5JNG3IBEfU5cQve2IgRpI9saeCr9Ggnz0YEjI2QTG/SQmr0NE+LY1V2ZpYSlUhhQSLf1ujUdcteYVCLvkOM6dPejQlY33+XIs5Y5U3ldsxDyksMHRah40bCgCFgBp0R7moyvHMeVDMjA4ruw8BUA2jxwPJlC5QYkmtLINoAqCYhYV/p39+ZtbYLWjVtTWd6LF5HIUsCBHPu/9RDKK2NVR/jOQw2UNOkCHeSbjuBXlwB1TcBfCT5+mofBYYZX/tncGZ5k2yTUvsZlzpjDpZY3cNt8l8kZY7rV3AXTNbP3yI/RPzjAPrjmaNM4rUgxHwGa+zZQ7CR7/PwXcc83dnV99X/PKqcXPjOkcw1duqy/qt2IcjUx0U4uOMHJtvU1eOWnpuWiD51+r/+wlOX77RUEziMs6d9CMkVEKhLqMB+42MUq8mZ5+z5taRrCa+10KVU9TSSJygayf+sncw6aqF3orPTOhA3rKfOkoBYQ3Rb1t1Ajrw5W1fMwqJabJCWfCTEHwMWTQJyybRqMwaMVvuXhKJnfzKnAco0x3ImY/AQX2dps68pjkyUG2fylV5Izjw+EsZ+bkmSCo3M4t4BfkHiU5hZRuOob1Pfqqv+eHpySCbl/t4GUy7AK1cxhTakG5DKS/2As8+uTvQFDcFP0hICBwj3su6p/HSAg62KQjJ361sV04CefIcY3luUMRlwXKOI3jUa9j/86FhZ/NLaUVk3qI58iI2jgymsIfZH8vNJ6wcnZiiy+jtDbEdlpVTri/ScaXa74Zb1fBKYLIigxmwsw8G/l8XdJnkTK7Ejm+51+/bKh3cwDrQCh49Rn7tDG8cx/tiAKIsNhjFuy3x8iABtc/jii5QDMRsrQFyVbJR69Ix5mMw8pHhy613ks66L5PG4z4U3DCjbQk/WCHi5jz3CGDBdwerRiaT8H0cxAB4mW8yk5vL44fYcEYgH0kt7MG7qGfDYawLDd6qwuk0tw6+r4KVpSxvfiDnbmA16yAEab7cI3TpuTAmAB3yIPMC/djBlk0Fshb+6HqZbJF4tYipb1WAsUrz+Yv9u0P92a7zUDeAbsT2tdlHn/EVC6n5TmLiaRGkLh4tM4vh9V56Gh0up/4bbz+1euR+oO2Tj4CrJsuDbH0F8h7vY1KCvuFKG/au71oBUj+CTzwa1MpaJs4l9kJ1BJ8m5Kj+uXG61H4ZZqD2ROdqV+kt9lyVB1ySWsAkzGruZeWwK3TfVk6aWgLT4SahJieVuvO/53dTq8rouJi4pk4B/FQrsBtBLL+EwLq6tP48ZxPa4jwPzohNXA/u8Vm/JiRXWsKbCQNR0KymdWQ8dPhjTX0ojE2YUn1VGw3qfNMdQa16l2fnsch6DgPOyywmlr2C/afuetHjUsJvy9x4asp324WUOtw6Xg1JtBepaCTT/dALHQTAx/vodSgMePzkg76IgDmvr98nB47IwuEB14dPy02B9T4eHLzV6QxAPUAB46qea4+4QYQGidPtTvuS8aZkp7b6xHbSKlyiS2o5rM9M/v+ihLyAm8VJuufpgnRgIqPgFF/pFyXp0RG1SESEsCw0mHpJRBJKRBxYoxX3294fkZ2nj6wGAx91f8a0oo0Ydm3ZPzEF5Fd3HskMoWER8xZepPBrFAfV7QmV5M/v6vfk2NvRgkRDBS/OOQLqncQjOhxyvGWPitkw6iXQicuK/kx7hp1UmdvO+9Ioi8j0ZmaTTyMQJG88sLuZqkFddoMbs6WAyL5XFdIk4p1qbdFTvPDqh1IJZcUXpnxiMq2cODv5+kPLDACGMCq6z1Fvfvl22OMmiRDuhSJXoJ2SPkb9dAUVKeTin/5bQb84YxALXxXlgxH1TzWfxpFMsjXgehwGH/6LKoCxDyo6PMnaAm1QijZ6tSqbQODK/JEF4F7ZcC2sdobq9Sc/WL7IEzJo/4SqBrcEGSuyIOCZHyS0WQ5SE1jsEXwTIHkgc+sDYei3mpXq3n7SDZFvdrBZV9X0AX7Dz5m0xyHKXZlDqKwgF3gvxSZFnM/Rxxg8e7hNBSRUmU1gv9BNnf4kAbjZPW4pUYvEd1izT3Ahowzkfbw3Cs4Esa7PCnDERFaYIsamSVVjw0aunHrrzNBCjxBBkdjZLSgCLOuE/nKWPKFIk1BMguxsh6taUuvlJG6aPVkqXXTE+/RJ7bIE2c7Qvb31D9ykdFhGtFWRTvmbsZ/lNoF9QP98v0luKJr7tk91aPTwZBYXHZGYjT6XrqROz+xhLahSg8ui4XVKgWD7mqM1nm9uouoq0XE3H1rEbpzuSl+sTpTg7uwwkcaAopB81rrEoIEnw5csfPGn/Q5HbZFaHKzIAX0JjXcR1j+i1Ajwg3vefCu5Faqc/NBYNE3f1qPvGCCckM5srP+sPyhL5tKcHR/HfkeZc1dQLATtY1yiWEfo6IYTAN3jjleBKw7xczDXrGtdAkM1+ZStMNomcFIulaEw2oCI4cfX+xUlT0sm2EeITVq6BQyROuZ7fwjarkqQjNjqRBL2PYckSL1pmFz2HL0mbgTvSV0nZu9z1TuXLNAhJwo9QK1BhJllfWTpPP8p7Fq1jto3bO5BsgVJF5i1f0qf/DUneXjgXafna33bNv2R9Xky7/IUY8B/KgD0WBVGoBT9vB/XGKR9Rmk78RFgEzUK/1om/hD2KiQ3FVhsvS8cM2iZs8pzjshAZ2nc+kFefjb4g3lBXrW/0nhh63NsJs0TOR/rLaT7X6UKtnQ2PNQMFXhvI+x9rBTp08eShFytrw/MulkENXwN+s3R90sQT72TZwoI4eB1GNRyk3NQAheISRYHHr1BBW9Gzn939dqy6nAxEK3cqzJQy+ci7Ct1ButZclKZB3BOr6jqTgFzqAqVT5bGaEGmxDZudOVqgm9n6RkT1k+54OmF4Fe1HD2CsXN+wiebT1J5EZmntJuKXSsho+/mzB9G+DjIwLZAadClFuxbNjj6S63b7z5dbw9oOvIy20sYVFbavaFg7XaAmNORKDzIKtMbNsnmf62zV6WAkVvbiBdl0wPnfT21g1wnsegiYOSCxEbLjTzRJ4xLQptT0bCGnVn5d3tdtEpAJW011c9Z4+HmW8FL/qkhzXsYo4iMWoTR0IGOFS8gOtAC9fu15VQ+NIT6T6zcGv7KRGkANXCI8r/CyxfOoxRQIcK0eT2N+bUWF2jZEnZn5+d3RNYJH5uJ2bdeyMgZOz90rTIc48BUu7yvE51q8EqpXcOJF4GR3m+2Fq28K59h0I+/OaWw0GFHXKC7QjUUbfv5KQIbmo8F7BzLCy5A3F7ginkenKierUZQ2ZSPm+UX3UMwNst5GED1g/yQ2gJrICUscUkmpNjW1cV3XhYpq2OwKC5bl3b1ZEesK0uzSpmwpVk3OLDSrpbV4bGlympljmrLoVnPq8w+j+d/l0iXjfR5FJgQEpTEy+b508gb4V29Ui5rsP+jXj1PRLu5KBDcrunbaetfY5EP/UxqzDVt4uE9j4ZlDTWcdMY3ncIR/ET0hZgQeApZQ4yIrs4GJwLWS1FTPXl2wbTa9Ci965hVsOSraH7vXqwsif8Kyoqaz2PUPr8/vH7MEa2yfYhwVhQpUA73XVQeTAM6M/NuDZy14ax22Q/xK8MvIIbYvEvZiwtg5pdCDZilnBkqBNbp2ZaKXTDQmhh/dn6sa622PsjDJXSMl41owsc11IVibnR4qzaNLFgj6SI+HlVHoTwnORPMP84LvjmwWtBavdYM/F/0aS40j97K13tIsAVAti8K5jPbWkccD/uyczKX9RXcz6td8R1d4epSk81gaKEDibtyDih3FybcsrMZ0gJneWnS7EgE+5zzCYeIJYD+cRNtWOtM8axQ0RznO+sTTJkugy/jw546Rei/1o0wyXe+7cKJcS5J15G3JwhWM62qK5JPMMfrmiLwyifsCHc9ZoVzTnSW3Ti6hV9+4nuLIY0yz7+emuEDypb+4ZICciMxCCJ3E7khjd/dz95vw0MrTbiTgq58YoXsH/xkncxH8jKN2UIenmrh1Husp9THrS1PSRe7UyslseuXIz2bn3TLcImxzG/bhclQQarnnXLYzCcT4aZ+Wy+u0dJnjAnVqRV+U2H+zR8miuEZ6ciyAgtTxBG/fgfmU3j6n2lpjSXgYUfeGARRhbdrBX0JNJ+VixFOSeJmM6Ha2I7ORQb8E5h4XdpjwP/20kvfPL9fcEDVY+iibZzWlcEYm8/nOri6ZRMNN8dwpLX+EQZUfIXW7EsVKvbdchhSI+bDlo9XH7MKNFMpuaojsZNcq1+npWHoIN+FWqWpbWDEvCfJtgOrPeTCBo1WIRaeGQlshXsOS7s1/61c8DpqPkupDmLQ9FFNTjAYV06GWkNffFTIFa36f4bD/A3Sz0mSKsJY3N9m3zmMH14F9KRH+fbtIGZf4s0Fh5ZYBWgqNsO3m1bynRitOA2bch5CAHbZuAYaAALR8fBo6ydxx7MV5a/taf17vpCqATY6skOOFSqBQCBi8kMVZBZEv4DFcRfB6Qyl/URG5U9oTEIjiA3wq+VzvlFq4dI54GhFV0t1OQuGXB9rcat3FC1dIDCR4mJP9aiuR/FcHeNiL/EQEifak4+uCazKuBJ52sAM2v0wmwJghiuLxIjT5oZvZiZzra0sOAlm/Gkd02UIOVfe/MSRG1D+eZ+6jmz9HxhwsX9N5UPz8V2O0rNlPbGs/GHljBS/Dxf1rHK8QVZX/JBAjCis5+4Y2kMiYsWJxV8LVMf/clt/r/Nj63Xrnyb5zObtULMKbC25oRxeVboexWE1m1OKXDQih/QWbOoasLx/OZbL/EMj6pFcTD7CJbsBclv42aj8gg+PT9z4CF2GNRso/iQdDmqiPpdSLHZjV8Z5jXUDMf5hW+8e2ynG5qAEbsYwXJClmw+xpD4zXzKg/TUfkRH+UYJD0MDluJ5BnKWwsVTX/t01FBX5T9WiNKGy9akqTpfoeZRwr51obIxntr3yBaKAU2oyrszmTyWNwUca8bDSnLKkZ5qszDAJb3qUu4VwuIzV7iTK5H9sg5wjk6bqve1tO1Hte7wElJeJeys+hikGiy7DnEHBOZTJLOwzzgFAQnU7ansmAfXWqc+TbLXgH5Z2SOTTY0Q9W9UX0goLAf4/qErpyL1UF74xrvJSAD4hevQsRuyYN+Nuxhp4Pj2fzN30Agu6ZG8WqGaRHSDNbqdn/6zvY0mLqlOB9+NWcnNhSFUxtjobzP03l/BIqjuEktSNa101s0aOLH0+TB7klbWZSBZWWS/CmwcupSMvlQvyxkVH1T39D4LSGqkbxbPQNZQub3X3u33N/Sc3qYrXeM/bbO02K6r7pMn5HP8hLkO3TMiK2x4pc/YmPkZT2IfWsMYvpA3UyRtXgjzQh5fmisfKew5z7YU5YT3rO/hAx+jzF7gBLbGnBS7wGjr1Qmo7LChp3xkb+ccXphoeOQl+SwlEcGDWuuqbVkuden5LM/HSXf/BBktih2wa30ZgNZq1hrbnPZjf6YPCSq7RFSUtja9k9eDN4Be+swHsVsZpVputwY5XB78whoE+Ze+8sAH09VIuxh/01lv+N82qJmxQYgi1/PKPPMEma61U7W3uEA/Y361pN/i6wvPb3vAzF/w3fhD5pdtXzzf8O7yJHVWz4muN+NF8wQb62BriaA6b+4IJ/rTUjpZtLUonW2vz5LSt5ygGklWJWzxQui2x2muuvZax1lntA1P0F93KhNCO09zwsh8g2AEfR0H41lHa9umks8jzTnJESPUAt7N9ixL7B5JaqbXyn2VUP50FJ8k1s9/yKsCKn2AyGHh7jkYuqfOv6RhKImBDeVpYGPX2Y8XWQbSg9fLk92KtS/1fQaPhM4eGNyQ+PVY4SkvrQpjqd13nNWWc8IBf4s3XCYAA0Ds10OL+yNR2l5vlfi0rv93lU3vdDlvcuW6gyCuB5EZ77eUTNOoVps5BnZTpeL/QT97hlDf9AsPxC93rPv2QyajCUr6m0QuJ6WnTJOF57uIvEtVqiopYxosSaitYsMD1RBc2Z90uY8qM8lcn1QLugXAeoZ+vkeI1WTItdaouZD3pOFifLz/+BS588o+TyAXl/YLkXMeScH/8dZvdLn7oS46wB5SvX/IC8IQxd9jWGrX5cNN2qO6bCEi4QJn4Rr/TLxvmqm6nADz2Cm65ITS+0plRC0UMRO0s1oiorBe9v4FPv04jrnu9qx165TaZJN5w1eASaguR6DCxvhT+EI9Zy0nPSTNS8mZ7uNtKeblbtSpUSxrJ700ZPkgD/omSrxFZr2WkosUS1fmMY2jwaM8W8x1FWcj3CULhHnVzHAZSIpnyMW4HoOztjbNkTC/QzA/RLpSIF/QTr76+wKT2gXbMOJniZkObGC7KN7EIQEMzsApZizgvogentGUPMjtKU6D/v17YIIcXQgFlnEbGOcc8cGb/Ca7sZd3VqpOwrmXb5GEXtmekVZemgPZpbNGOBF+/LwQkpjiVfZg0ESO70O1Kbrkq+3umbh6tlZugHq8j6LUCtN7aie107pIK+mTcWyVdOiJN3wwHVNe3x9SQvn0jyCVjP2ndCBv+2n0iJwY47BL+TcCe7zrdxeEqTD/wSiLhK9ISRcq1MtOeMGZSuebDOUuhHY465b5/TT791qbZb0P7xrN0L8uH1xmJGulnoDOnaAXrj9+QhUjiM5jOikC0EWbu3mO7JmwhKVw15l0kiRC2uti8SgxgYCTOKJLqY6hiUP/biQy52GkXnUbvuUNX4OnqxXVBpNvYmxA9RUuurH6HS2JOOK5rcPrsC9WinAKcDPIhkCdREb3pnOFgZSU7kdqzYpeX4ZjJLupNzy2Txiz5buV6Sdri/UuXzEys5yilzanN3ydt67LHugwzS+aoqhZlsuRVIACKapUYIe6tClN9DPzv59ob1TxN9O2mXeavxYO/FAgew9CViCtJZCr3nVfXbxi6e3IfimuaIYpVBJqFJ1d9k/SRwbc7dVngSqyESbLOVx3tG8a0TvcSyxlxZGHqeIoJPvoDfR1v6CybZDv9prYmOU8IdiINyLXOcA4bHK4z5prWy9Bs1KRMBLwCkBTw3IcjuQklUAxB4ky432VD9J7oIB0CYW+xNv1gRX1KlIahNABB6MLIL8KRP9m57GTLoF98fJmaN7VzzEz2tmBvvHu0NyhFNWPmqty3ugZx/Xjz9oITesFiJ2vNStJyfyYgYCrPvK8v9vTZgOfPETeLRekkDq8ZY67iXdULQowMY3jJooeAKqrcEEOz53rXAlBGTfJ356ODC5ZFHJ6FPn6jUnyhTl5nBlQsXqbGbM6NiqoKwRuIkmat7PqISvrU9abdFB6XjzcS2lhc+DO9aegghlHFI9Uyyp/NLERF1ghFlo/isQmITRbgCtRNj6tFG4yy3dlvTUAfRa0UPKCXlNs/EvDuNHzPOSVTWJJmXXcc9gOT9t+rR1IR1hHilOA0sjJdnGaefuFrsNB2AJU2b9+B06NZoRRgtjBwJ2wepIvq559WGIQwBT3Os1dUeo6j3nDhveER3vxRcjqcitxLoABrRnOQmzNrXFJzlbrcNd4Aefz3xDNUSHRYARmvwesYTid5zjE3y7Esf13pcW9oLlg6/6F/KPcwfBVscWV5t//UXvyswtfv7rGzJfpbIWkUtYTnBC01R9rId2tCS6+uz+CmQQHYx4z+TYxeqQilWdoAqGfnXgrtzvSIyO7IyyhGjaFq19Ird/J/Aql6yI2MovjTn/6PZHC90M0JU1BAfmRGiB0KKSO0o74qG7A/6t/2SW/vLoNd4Dxipk5jOfuazmCqc4dPTg+rcqok2GluC8lF8gmSAX7+34m18+FUjwbxgmu3T0sGsXwNXvuVIZGazC234MGkDNNPSytUGyfH4bpCDspH3j8bzAzuLznskHd/IlQSbhhg8xW2cVeYN3e8LZ5opC6dVjkAk+tQj5XwarRLCwkVWJNzSc8fMQS9e2B4+3bFDOvufRi/FPCbik2lPK2xR9LxbHLAW11EhKQdXK+jeQYE8hJ3wO75JGsb1tVqtX+KYjGRcezFMBkjnC0rbmouMw2nXjaFtUBO9+Gx2IrPOWT3Wk9QcKpJznLHmH40RfppsqYExwaN59wmI6VR+UbhDlnS5nG1Oh4RSD5UjH4FckjcRbshzuektvg9yy4obR+5kREkTJu+pDSIFe1zf9xWuJaprdbFYJkr5ZUqKrcAaoXfENh+lbrXK9aUJ2aebCquBRHXtXGnJdDB0YjNfhfa9XTkCqkjuNTbTKAoLHVMDbfd8NF7yqxH7ZKyMKsqP88bH6K00ttV7eOof2hfrgdjHi+Mtp8xcCf5kk54tnno7hwffpEWYtH14KKOKpXRRvhcxoeVD4DLoYxj6DifNPhm7cjWSZ4PUO9Itz3gvniIaDXlt5VCvoMpzPD17JZpUbh6JsH+z76uauailpt9bYXHFtwjDCVUic5COP11dJuz3CNDIvN/oT6sicUd9jClO96MLo3mPpF1qpndDXEkpEOxXuI5i9k+myFKSSS5gxZonTR8LqTwepqQKq7ELU0qFc4qcOnSJK80FHIuGiY/ewOWJB3Vhoc7BpFq2VipmOUCRIsdxI5j/g8kF4AM1qDEQuras72UGyyXaHEpcsjKGKYza8efDUVFoAO63vZZa4TgCoqdKSogky0yjbTqVEypnvxdmULjhHHpIMzMAZDJW3mm0T+obVRSJHtn1KpCKkIJHMMTZ1MvJrE1XpTq+s0iDcNkhnvVJHYn8FJ/YEqSQfncMU6NeZ2D1Me3jMJTWT3rmXZj9YfCq6yHfJP5scj4ZTqrehfzaZ7M5ZkeDwgiYWcW1ll2g0vLLpROVLqBw15HlMCNwaEHhJcCFt4od4KkvplZB7QkqsKV48UwR5YahAKzRxq+fTloWchJZeLBAUYbPX+7EnIALfClrxwKnb88GO9LaStMoaruwx2cImhtPnQivbgTYsLz+rL2eeY8yYra1be1jAfTGoTnua0+ALA2z8gvmDzkkXOtCV5bvi1eh7kF0zRrYsS+PK/zyc3y/1cbpQETLELON/Lulqrh75giST9kJA9HcBm1eq4XjRVYuGaYC4xk/8hRg8h3CDRQFsxKdntSu5mpvZNI445JG0pw6vTy12gvcY0mGaHMufEwYCqZGfizqQPINl8T5BsdJnH4uwanOzTVuR84eCCi16lrGzTfzgDt3WXZa5HPEBMHZCA5ywHdYfdB90RFswFE5xd9Eve+GCbzeKoXIXLsZrUnRsh2CoMIZ7CEegX3/M7Xqo80g4VnIu3ktKi+sZCrEEhK0iSti4JWMf6Ekkpu9xg0daqQjdyUbtHen/Kks2InxIHhgBOmiM4tLSqjn6XySRsLwN20ir7cew6dYbgls8/ixUexA51k9B6Ryt51JnvJB2yESkeoivV0nrV52z6rk4vIz/0jE5PGzQECUmoVOKJF/PAmGlaehEgXzD0ChV5KESg2QSn0hvtm6iltDIo75qPT36pZFNNpiur3nZWUfTMQRBpGJlNGig+4ILV10MQR6D4StHPaidzeT6Q2yAL3OP9XJT8jGlNby8IPKq/tE9JClNxO7luuTIQeNcFBpZ7AsLx8sYZXyOzxK/42vmybpEmPCaOX12K1lERLTSI3iY6bD1FwKzNvlfU4VPfMeeZuwY66SuIpGSza7LBryK+PJy2ibMlgpJ28V9ziQ9z7ZOdr+G8TbV/y5MAI7ULZPWdYw4xHsbq1xUd6k1WDqNxa6fWUt1tcKlICdJiCACIb4zyZfzaSAmc2N60sRNnRgcXCf7/Y6fNFjLD0cLOjMaDV8GxzGpif6pBWMi/rA1FA0DSYanZYUmhs0exKKlD8tD4wQLSpUOSrHe5hwK4+4BIRzEnd1Pudz9oYJn9qDAKdV3FVS4e0vowpC81JwLnis5Kl2Qb/ka9ip6BEbeeWmGY+YAkSBMA6i+7HD45PzWxtMca1dIlavnJ8KG+UInfZ80F3oNNEsehTXG0Y/k1dgt8ZqEHGwpLww9vB8Nr6gcyXA4PsLpowQOKEgKH0N/MsIyxv2FCuEqqq0Y06FZOO+QcucCHAQs/tPglkhM49oT7fA//Ih1cFNIGNxGfr/6ZTQ5LrnEAZ2JHSPYR1WvvpdNo3C/OMZl6WkIq4fHDYG530FIRXoK2gqQx0mLmsHJ8a9DPhVkSDJ0lVG"
            }
        }
    }
}
```

#### Range

- Source page: `Maintenance/IPCMaintenance/IPCParamManagement/Range.html`
- Purpose: This API is used to get IPC parameters range for [System > IPC Camera Maintain > Param Management* page.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/IPCParamManagement/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
    }
}
```

### IPCMaintenance / IPCReboot

#### IPCReboot

- Source page: `Maintenance/IPCMaintenance/IPCReboot/API.html`
- Purpose: This API is used for get IPC parameter range, get IPC parameter and reboot IPC.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/IPCReboot/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Maintenance/IPCMaintenance/IPCReboot/Get.html`
- Purpose: This API is used to NVR get IPC parameter.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/IPCReboot/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
    }
}
```

#### Range

- Source page: `Maintenance/IPCMaintenance/IPCReboot/Range.html`
- Purpose: This API is used to NVR get IPC parameter range.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/IPCReboot/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
    }
}
```

#### Set

- Source page: `Maintenance/IPCMaintenance/IPCReboot/Set.html`
- Purpose: This API is used to reboot IPC.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/IPCReset/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "password": "1111qqqq",
        "channel_info":
        {
            "CH1":
            {
                "reboot_switch": true
            }
        },
        "base_secondary_authentication":
        {
            "seq":1,
            "cipher":"r8zCQd+EQpuhKY2bKSZhEK/mkpeEzTRVlgDwiepew8k="
        }
    }
}
```

### IPCMaintenance / IPCUpgrade

#### IPCUpgrade

- Source page: `Maintenance/IPCMaintenance/IPCUpgrade/API.html`
- Purpose: This API is used for get parameter for Remote Setting > System > IP Camera Maintain > Upgrade page,get IPC upgrade token and IPC upgrade.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/IPCUpgrade/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Maintenance/IPCMaintenance/IPCUpgrade/Get.html`
- Purpose: This API is used to get parameter for Remote Setting > System > IP Camera Maintain > Upgrade page.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/IPCUpgrade/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `Maintenance/IPCMaintenance/IPCUpgrade/Range.html`
- Purpose: This API is used to get parameter range for Remote Setting > System > IP Camera Maintain > Upgrade page.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/IPCUpgrade/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Token

- Source page: `Maintenance/IPCMaintenance/IPCUpgrade/Token.html`
- Purpose: This API is used to get IPC upgrade token.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/IPCUpgrade/Token
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{
        "file_name":"CH56XN_F64M_SF_ENU_V1.0.1.1.B000170100130f_230104_r19922.sw",
        "file_size":74328284,
        "ipc_channels": [1, 2],
        "upgrade_head":[220,39,110,4,32,2,0,0,125,15,88,1,187,40,116,7,57,218,176,153,74,21,0,172,191,216,204,132,183,161,245,241,131,212,116,145,237,107,37,83,117,253,79,245,70,166,0,98,57,132,230,96,192,170,31,171,170,119,197,49,224,159,237,59,68,132,58,64,207,3,113,130,18,122,63,232,12,58,32,96,24,3,195,186,116,97,1,58,68,188,175,216,209,5,67,125,235,117,46,208,211,66,224,204,25,198,32,103,24,174,163,60,71,110,121,186,162,20,109,46,188,232,226,186,228,188,201,227,254,160,201,97,143,208,42,47,144,237,100,157,107,119,142,158,166,9,89,133,77,163,55,200,104,62,188,122,224,240,88,170,31,178,117,49,228,3,96,231,102,241,51,193,127,176,215,198,218,16,45,164,143,78,223,209,144,160,91,251,51,186,85,68,159,234,209,88,151,136,8,255,202,71,72,56,87,19,94,218,30,60,180,12,144,248,161,111,223,2,187,181,188,241,108,78,18,64,221,152,200,158,192,33,218,203,241,90,186,155,255,233,181,255,104,230,166,115,69,223,35,101,255,15,87,53,41,84,161,66,180,246,10,205,249,121,78,55,88,88,88,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,109,86,147,204,1,0,0,0,204,0,0,0,0,0,0,0,196,0,0,0,8,0,0,0,2,0,0,0,86,50,51,48,54,50,53,0,3,0,0,0,86,50,51,48,54,50,53,0,4,0,0,0,86,50,51,48,54,50,53,0,5,0,0,0,86,50,51,48,55,48,49,0,6,0,0,0,86,50,51,48,55,48,49,0,7,0,0,0,86,50,51,48,55,48,49,0,11,0,0,0,86,50,51,48,54,50,53,0,12,0,0,0,86,50,51,48,54,50,53,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,70,30,16,114,252,150,59,22,155,67,56,37,171,172,67,211,206,219,231,92,106,154,226,87,34,19,0,253,199,225,202,91,182,160,106,100,62,243,118,123,11,29,214,254,45,249,151,36,40,255,98,89,157,108,189,249,71,155,142,170,1,166,18,141,161,154,0,46,229,115,207,169,82,57,219,201,95,128,179,104,63,232,170,41,175,194,92,189,2,120,55,0,0,121,122,228,6,131,220,198,146,151,101,141,68,84,110,188,50,124,36,244,101,160,129,83,107,27,75,154,24,52,146,183,152,9,112,119,80,21,99,83,24,63,46,64,159,52,40,236,204,48,197,151,254,155,103,159,126,175,161,120,243,59,25,98,229,212,3,45,6,218,208,66,2,217,217,18,250,157,240,157,45,222,243,49,211,165,204,193,191,225,87,7,147,196,247,235,178,29,68,166,225,175,187,78,123,203,5,127,77,237,52,204,176,168,172,252,98,116,158,230,76,77,23,255,194,159,57,221,34,38,176,8,146,49,40,80,201,124,47,63,228,148,32,70,3,112,62,216,44,13,114,132,180,51,81,230,242,16,116,0,246,178,236,123,166,244,11,184,74,78,177,90,181,186,244,66,253,112,37,139,89,92,179,190,7,137,237,191,73,193,176,244,254,114,100,128,64,253,245,58,208,169,36,146,209,73,175,59,196,153,185,141,49,26,233,154,150,79,173,58,245,15,150,87,88,12,27,201,33,105,120,4,184,101,78,146,61,9,210,253,63,119,174,130,219,219,36,97,4,155,1,128,125,189,170,119,197,211,200,166,105,70,48,113,173,180,126,237,150,184,110,71,87,113,21,104,141,197,164,202,224,253,237,15,76,12,210,238,191,69,9,198,24,208,233,40,238,207,26,161,41,129,51,203,24,222,167,147,32,58,102,16,144,137,51,111,207,216,163,115,132,242,240,20,177,97,86,185,128,250,21,98,91,97,124,201,107,89,215,150,72,60,56,251,135,115,222,55,196,183,36,192,75,72,108,130,70,97,170,69,116,142,131,78,85,12,182,139,15,150,148,241,77,242,222,53,230,36,220,115,124,19,100,223,226,13,104,56,61,126,87,29,137,106,179,71,187,179,103,244,71,166,5,172,119,200,64,104,254,44,82,30,156,185,113,71,44,61,112,55,122,106,162,143,176,178,109,149,99,113,158,50,37,222,84,227,226,253,73,94,174,53,205,97,148,141,118,108,252,60,235,158,147,70,81,85,118,89,163,22,145,218,238,205,205,25,141,104,16,36,100,76,217,205,141,112,34,85,149,155,137,203,231,186,139,137,171,124,154,3,25,63,34,225,246,209,145,69,96,3,94,124,120,36,178,194,193,153,192,95,12,61,14,73,171,212,8,156,68,3,56,191,114,162,12,35,4,23,190,8,221,138,145,105,89,112,153,63,215,76,169,102,87,159,158,177,11,114,97,136,84,4,92,178,211,21,209,141,35,52,17,179,255,167,86,77,148,29,128,53,94,74,70,89,19,107,146,138,50,246,151,116,45,92,222,107,181,19,149,129,245,19,133,30,10,80,62,129,149,228,242,83,89,245,79,204,143,11,11,71,63,211,28,42,178,43,52,225,9,157,174,162,239,238,245,122,253,91,231,206,162,231,217,204,246,12,254,31,163,175,132,150,33,78,81,224,65,53,88,18,185,132,167,171,52,198,246,108,195,197,223,185,182,41,27,151,1,161,193,88,169,110,151,104,143,29,159,179,131,112,5,150,21,150,203,211,181,29,88,4,96,124,106,240,213,224,228,159,209,195,2,151,242,242,17,85,238,36,196,174,76,115,231,123,116,237,212,213,106,199,229,134,235,196,244,221,32,146,87,235,229,160,195,182,209,89,128,75,137,134,7,205,147,206,219,171,5,195,27,215,88,230,156,205,241,120,182,2,98,88,65,110,40,34,42,79,191,222,25,61,37,119,195,168,203,150,255,107,247,150,123,54,185,156,205,5,26,74,114,241,28,26,214,72,100,162,52,64,114,240,14,255,12,205,175,182,105,242,26,34,188,195,36,230,246,248,3,42,106,162,130,176,106,96,94,5,161,148,117,235,213,89,202,124,218,80,241,58,189,200,157,171,132,142,125,118,57,136,199,179,155,207,169,127,213,229,75,207,141,43,208,222,146,49,180,53,210,66,176,224,112,119,12,73,97,129,135,191,124,133,95,18,166,226,179,153,141,85,162,143,139,221,148,33,181,120,34,173,23,198,239,200,219,119,118,76,39,29,133,158,157,253,157,124,86,240,62,49,193,111,66,216,127,33,146,133,112,14,36,104,35,30,157,147,223,116,249,232,30,7,40,168,21,129,66,188,112,52,104,25,118,59,222,126,252,136,37,218,73,131,203,88,121,191,13,146,203,206,252,89,148,248,54,49,99,183,65,82,70,217,255,139,111,183,185,17,13,166,82,167,90,64,107,156,96,47,125,16,197,105,96,226,243,107,7,149,165,77,158,146,21,248,50,105,55,251,161,121,46,30,231,130,226,96,198,240,76,10,27,3,107,190,133,217,21,52,233,157,246,202,205,194,36,148,56,37,64,12,249,150,116,35,27,42,86,72,183,201,237,84,85,17,6,222,47,207,178,31,144,88,165,173,126,208,120,8,53,160,79,249,229,104,97,195,62,47,87,192,109,112,101,86,79,65,234,104,43,29,123,58,236,67,4,235,56,3,212,233,212,100,5,118,161,200,146,177,52,64,170,129,220,141,185,227,1,113,131,87,24,141,225,114,89,200,166,27,41,241,49,161,92,65,97,244,97,203,178,121,147,205,202,229,172,210,86,222,39,59,151,179,169,195,4,173,199,255,83,19,142,171,78,117,59,144,239,0,247,54,201,73,22,179,20,220,119,214,110,87,91,174,135,28,203,198,83,76,229,249,148,105,227,136,122,204,138,126,92,64,196,171,125,141,1,5,216,149,40,39,201,172,33,81,38,146,125,144,75,208,185,219,126,244,203,217,97,169,192,175,163,134,43,97,182,93,209,193,67,66,237,29,64,105,14,120,94,225,158,43,64,210,226,160,125,216,21,70,254,50,43,243,28,31,89,231,127,91,212,210,17,110,175,126,249,16,63,238,18,112,143,240,200,173,158,18,107,75,180,91,209,117,238,95,67,174,133,131,242,238,27,250,17,84,3,210,125,219,114,18,230,7,54,215,147,156,137,25,126,114,57,241,179,35,136,81,95,148,191,210,203,41,159,116,14,156,165,254,98,12,104,146,220,56,67,209,10,38,149,153,243,105,134,137,197,200,98,78,182,195,236,121,106,114,179,119,81,4,214,191,107,97,215,207,135,18,228,155,165,70,47,40,92,215,246,31,164,59,98,170,91,76,159,77,142,103,234,139,115,231,162,194,208,43,50,196,185,238,173,34,28,158,33,127,232,223,175,34,143,145,149,182,37,152,108,201,215,83,249,37,178,183,28,84,229,53,240,101,244,44,207,103,221,238,10,103,153,34,138,175,147,155,71,139,110,135,89,49,126,157,55,179,0,6,171,183,48,242,11,230,178,126,79,108,83,30,73,196,100,194,23,134,140,232,61,76,238,46,32,105,178,179,170,194,20,115,7,59,230,247,226,224,139,67,137,241,150,130,193,220,79,44,50,177,81,8,85,202,10,200,105,226,196,113,126,164,139,6,189,244,126,251,190,210,221,81,61,16,225,244,241,77,182,14,201,35,182,112,40,2,130,6,190,155,45,25,79,119,148,25,165,238,190,100,249,84,143,20,201,181,218,255,34,162,96,11,224,156,71,197,20,99,130,158,106,63,35,126,11,71,203,249,232,70,65,102,220,7,255,56,252,240,64,56,227,56,255,186,250,251,195,177,210,95,233,109,109,109,216,113,147,96,174,72,97,222,92,203,216,224,5,52,164,56,214,84,122,27,86,105,237,235,81,87,5,86,222,60,120,247,3,86,137,210,35,11,196,243,196,175,2,142,58,36,193,113,96,154,95,102,153,183,171,49,8,34,50,95,208,195,91,202,182,43,151,253,55,224,168,69,72,215,31,236,41,114,188,195,215,30,226,82,115,244,123,206,95,200,245,204,247,246,207,38,140,207,98,8,116,221,235,108,255,186,146,68,231,226,16,22,80,247,7,206,94,250,127,189,186,151,109,18,227,34,68,86,186,141,124,171,183,149,154,110,233,11,25,56,249,85,46,137,111,108,87,83,185,77,19,46,58,135,214,58,115,27,116,87,181,255,122,109,195,216,122,127,174,1,168,33,135,128,65,19,43,31,253,127,6,76,126,187,26,173,34,102,223,92,42,47,136,132,128,127,9,164,27,194,70,152,126,192,194,2,55,145,132,185,42,238,218,239,126,232,221,103,130,69,90,220,150,79,193,195,38,106,241,55,228,167,225,48,65,101,171,120,235,30,180,50,211,145,60,255,182,143,103,96,78,106,195,123,141,145,36,78,226,213,224,196,165,46,176,233,8,143,89,202,43,14,62,231,53,15,114,94,113,50,159,168,206,228,6,24,183,91,130,12,151,141,242,162,44,15,12,31,138,182,210,243,29,7,236,127,100,205,69,79,212,8,175,21,199,61,200,15,192,113,159,104,167,85,204,228,81,23,150,198,161,200,133,194,236,72,200,237,226,171,187,188,217,106,21,19,207,61,126,126,63,121,228,20,145,189,249,200,138,72,167,211,129,123,81,103,138,52,187,7,58,175,28,21,209,233,249,137,4,159,114,17,208,142,189,93,180,44,248,43,135,215,151,26,184,78,227,118,154,219,90,71,84,141,101,130,89,221,164,156,155,110,247,169,152,159,13,153,82,53,120,212,226,127,206,223,180,221,121,217,51,53,110,193,104,109,136,145,13,154,164,138,25,123,43,127,6,255,237,254,22,168,240,59,130,104,70,48,251,14,115,238,85,176,110,79,186,90,225,150,48,217,87,19,79,38,216,181,50,164,100,186,133,229,174,14,34,32,111,102,143,3,30,42,115,226,235,93,3,230,2,66,34,48,128,238,13,103,14,62,27,113,117,186,149,139,89,161,138,252,253,196,164,4,177,174,134,14,195,50,151,222,197,64,124,124,69,123,190,141,247,219,1,33,68,43,252,240,34,67,2,107,61,75,61,180,63,250,244,27,40,29,77,192,45,192,190,213,149,107,13,175,217,34,106,100,127,156,177,27,225,42,66,199,90,240,45,188,153,48,42,138,241,164,106,168,163,206,255,63,71,115,251,73,141,246,245,124,92,134,140,210,219,47,216,133,188,17,242,46,247,244,39,161,94,162,63,153,41,144,211,67,164,181,235,58,25,224,5,130,190,68,229,123,235,34,4,141,109,120,74,131,250,66,94,186,33,109,68,153,147,200,247,121,135,91,153,118,83,47,252,212,91,50,238,101,49,203,124,63,39,48,101,160,213,87,224,145,109,126,194,29,163,157,123,179,116,34,192,248,171,97,53,87,253,100,147,14,93,42,173,58,144,162,143,85,229,92,185,220,158,227,85,186,105,76,180,248,140,86,86,94,183,225,49,99,222,58,39,156,51,18,90,192,2,67,45,110,185,73,69,5,177,167,173,215,230,251,89,49,158,203,182,38,48,255,128,174,57,194,203,166,168,178,7,71,85,49,197,48,114,78,157,202,145,193,142,101,158,48,164,166,112,251,31,207,46,245,129,62,46,53,100,106,253,175,177,216,177,167],
        "base_secondary_authentication":{
            "seq":2,
            "cipher":"FWRsfpB05p/NfdTleipoBR1d06/dZA2xO8cDJiF4CYM="
        }
    }
}
```

#### Upgrade

- Source page: `Maintenance/IPCMaintenance/IPCUpgrade/Upgrade.html`
- Purpose: This API is used to IPC upgrade.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/IPCUpgrade/Upgrade
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{
    }
}
```

### IPCMaintenance

#### UpgradeErrorCode

- Source page: `Maintenance/IPCMaintenance/IPCUpgrade_Code.html`
- Endpoint: Not explicitly documented in a request sample on this page.
- Request Body (JSON): No JSON request body sample was documented on this page.

### IPCMaintenance / Load Default

#### Load Default

- Source page: `Maintenance/IPCMaintenance/Load Default/API.html`
- Purpose: This API is used for NVR get IPC parameter Remote Setting > System > IP Camera Maintain > Load Default page and reset IPC default parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/IPCReset/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Maintenance/IPCMaintenance/Load Default/Get.html`
- Purpose: This API is used to get IPC parameter for Remote Setting > System > Maintenance > Load Default page.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/IPCReset/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
    }
}
```

#### Range

- Source page: `Maintenance/IPCMaintenance/Load Default/Range.html`
- Purpose: This API is used to get IPC parameter range for Remote Setting > System > IP Camera Maintain > Load Default page.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/IPCReset/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
    }
}
```

#### Set

- Source page: `Maintenance/IPCMaintenance/Load Default/Set.html`
- Purpose: This API is used to reset IPC default parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/IPCMaintaint/IPCReset/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "password": "1111qqqq",
        "channel_info":
        {
            "CH1":
            {
                "reset_switch": true
            }
        },
        "base_secondary_authentication":
        {
            "seq":1,
            "cipher":"r8zCQd+EQpuhKY2bKSZhEK/mkpeEzTRVlgDwiepew8k="
        }
    }
}
```

### Load Default Parameter

#### Load Default Parameter

- Source page: `Maintenance/Load Default Parameter/API.html`
- Purpose: This API contains APIs for getting parameters for Load Default and loading the system default parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/Reset/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Range

- Source page: `Maintenance/Load Default Parameter/Range.html`
- Purpose: This API is used to get the parameter range for Load Default page.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/Reset/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
    }
}
```

#### Set

- Source page: `Maintenance/Load Default Parameter/Set.html`
- Purpose: This API is used to reset system default configuration.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/Reset/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "base_secondary_authentication":
        {
            "seq":1,
            "cipher":"r8zCQd+EQpuhKY2bKSZhEK/mkpeEzTRVlgDwiepew8k="
        },
        "channel":true,
        "record":true,
        "alarm":false,
        "network":false,
        "storage":false,
        "system":false
    }
}
```

### Log

#### Log

- Source page: `Maintenance/Log/API.html`
- Purpose: This API is used for getting the system log information.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/Log/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Search

- Source page: `Maintenance/Log/Get.html`
- Purpose: This API is used to get the system log information.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/Log/Search
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "start_date":"07/05/2023",
        "end_date":"07/05/2023",
        "start_time":"00:00:00",
        "end_time":"23:59:59",
        "main_type":"All",
        "sub_type":"All"
    }
}
```

#### Range

- Source page: `Maintenance/Log/Range.html`
- Purpose: This API is used to get the range of system log information parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/Log/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

### SystemUpgrade

#### SystemUpgrade

- Source page: `Maintenance/SystemUpgrade/API.html`
- Purpose: This API is used for getting system update token,upgrading system,system version check,system component version check,getting component upgrade token,upgrading component.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/SystemUpgrade/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### ComponentToken

- Source page: `Maintenance/SystemUpgrade/ComponentToken.html`
- Purpose: This API is used to get component update token.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/SystemUpgrade/ComponentToken
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "file_size":74328284
    }
}
```

#### ComponentUpgrade

- Source page: `Maintenance/SystemUpgrade/ComponentUpgrade.html`
- Purpose: This API is used to upgrade component.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/SystemUpgrade/ComponentUpgrade
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{
    }
}
```

#### ComponentVersionCheck

- Source page: `Maintenance/SystemUpgrade/ComponentVersionCheck.html`
- Purpose: This API is used to component version check upgrade(NVR upgrade ipc component version date check).
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/SystemUpgrade/ComponentVersionCheck
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{
        "file_size":74328284,
        "file_data":[220,39,110,4,32,2,0,0,125,15,88,1,187,40,116,7,57,218,176,153,74,21,0,172,191,216,204,132,183,161,245,241,131,212,116,145,237,107,37,83,117,253,79,245,70,166,0,98,57,132,230,96,192,170,31,171,170,119,197,49,224,159,237,59,68,132,58,64,207,3,113,130,18,122,63,232,12,58,32,96,24,3,195,186,116,97,1,58,68,188,175,216,209,5,67,125,235,117,46,208,211,66,224,204,25,198,32,103,24,174,163,60,71,110,121,186,162,20,109,46,188,232,226,186,228,188,201,227,254,160,201,97,143,208,42,47,144,237,100,157,107,119,142,158,166,9,89,133,77,163,55,200,104,62,188,122,224,240,88,170,31,178,117,49,228,3,96,231,102,241,51,193,127,176,215,198,218,16,45,164,143,78,223,209,144,160,91,251,51,186,85,68,159,234,209,88,151,136,8,255,202,71,72,56,87,19,94,218,30,60,180,12,144,248,161,111,223,2,187,181,188,241,108,78,18,64,221,152,200,158,192,33,218,203,241,90,186,155,255,233,181,255,104,230,166,115,69,223,35,101,255,15,87,53,41,84,161,66,180,246,10,205,249,121,78,55,88,88,88,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,109,86,147,204,1,0,0,0,204,0,0,0,0,0,0,0,196,0,0,0,8,0,0,0,2,0,0,0,86,50,51,48,54,50,53,0,3,0,0,0,86,50,51,48,54,50,53,0,4,0,0,0,86,50,51,48,54,50,53,0,5,0,0,0,86,50,51,48,55,48,49,0,6,0,0,0,86,50,51,48,55,48,49,0,7,0,0,0,86,50,51,48,55,48,49,0,11,0,0,0,86,50,51,48,54,50,53,0,12,0,0,0,86,50,51,48,54,50,53,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,70,30,16,114,252,150,59,22,155,67,56,37,171,172,67,211,206,219,231,92,106,154,226,87,34,19,0,253,199,225,202,91,182,160,106,100,62,243,118,123,11,29,214,254,45,249,151,36,40,255,98,89,157,108,189,249,71,155,142,170,1,166,18,141,161,154,0,46,229,115,207,169,82,57,219,201,95,128,179,104,63,232,170,41,175,194,92,189,2,120,55,0,0,121,122,228,6,131,220,198,146,151,101,141,68,84,110,188,50,124,36,244,101,160,129,83,107,27,75,154,24,52,146,183,152,9,112,119,80,21,99,83,24,63,46,64,159,52,40,236,204,48,197,151,254,155,103,159,126,175,161,120,243,59,25,98,229,212,3,45,6,218,208,66,2,217,217,18,250,157,240,157,45,222,243,49,211,165,204,193,191,225,87,7,147,196,247,235,178,29,68,166,225,175,187,78,123,203,5,127,77,237,52,204,176,168,172,252,98,116,158,230,76,77,23,255,194,159,57,221,34,38,176,8,146,49,40,80,201,124,47,63,228,148,32,70,3,112,62,216,44,13,114,132,180,51,81,230,242,16,116,0,246,178,236,123,166,244,11,184,74,78,177,90,181,186,244,66,253,112,37,139,89,92,179,190,7,137,237,191,73,193,176,244,254,114,100,128,64,253,245,58,208,169,36,146,209,73,175,59,196,153,185,141,49,26,233,154,150,79,173,58,245,15,150,87,88,12,27,201,33,105,120,4,184,101,78,146,61,9,210,253,63,119,174,130,219,219,36,97,4,155,1,128,125,189,170,119,197,211,200,166,105,70,48,113,173,180,126,237,150,184,110,71,87,113,21,104,141,197,164,202,224,253,237,15,76,12,210,238,191,69,9,198,24,208,233,40,238,207,26,161,41,129,51,203,24,222,167,147,32,58,102,16,144,137,51,111,207,216,163,115,132,242,240,20,177,97,86,185,128,250,21,98,91,97,124,201,107,89,215,150,72,60,56,251,135,115,222,55,196,183,36,192,75,72,108,130,70,97,170,69,116,142,131,78,85,12,182,139,15,150,148,241,77,242,222,53,230,36,220,115,124,19,100,223,226,13,104,56,61,126,87,29,137,106,179,71,187,179,103,244,71,166,5,172,119,200,64,104,254,44,82,30,156,185,113,71,44,61,112,55,122,106,162,143,176,178,109,149,99,113,158,50,37,222,84,227,226,253,73,94,174,53,205,97,148,141,118,108,252,60,235,158,147,70,81,85,118,89,163,22,145,218,238,205,205,25,141,104,16,36,100,76,217,205,141,112,34,85,149,155,137,203,231,186,139,137,171,124,154,3,25,63,34,225,246,209,145,69,96,3,94,124,120,36,178,194,193,153,192,95,12,61,14,73,171,212,8,156,68,3,56,191,114,162,12,35,4,23,190,8,221,138,145,105,89,112,153,63,215,76,169,102,87,159,158,177,11,114,97,136,84,4,92,178,211,21,209,141,35,52,17,179,255,167,86,77,148,29,128,53,94,74,70,89,19,107,146,138,50,246,151,116,45,92,222,107,181,19,149,129,245,19,133,30,10,80,62,129,149,228,242,83,89,245,79,204,143,11,11,71,63,211,28,42,178,43,52,225,9,157,174,162,239,238,245,122,253,91,231,206,162,231,217,204,246,12,254,31,163,175,132,150,33,78,81,224,65,53,88,18,185,132,167,171,52,198,246,108,195,197,223,185,182,41,27,151,1,161,193,88,169,110,151,104,143,29,159,179,131,112,5,150,21,150,203,211,181,29,88,4,96,124,106,240,213,224,228,159,209,195,2,151,242,242,17,85,238,36,196,174,76,115,231,123,116,237,212,213,106,199,229,134,235,196,244,221,32,146,87,235,229,160,195,182,209,89,128,75,137,134,7,205,147,206,219,171,5,195,27,215,88,230,156,205,241,120,182,2,98,88,65,110,40,34,42,79,191,222,25,61,37,119,195,168,203,150,255,107,247,150,123,54,185,156,205,5,26,74,114,241,28,26,214,72,100,162,52,64,114,240,14,255,12,205,175,182,105,242,26,34,188,195,36,230,246,248,3,42,106,162,130,176,106,96,94,5,161,148,117,235,213,89,202,124,218,80,241,58,189,200,157,171,132,142,125,118,57,136,199,179,155,207,169,127,213,229,75,207,141,43,208,222,146,49,180,53,210,66,176,224,112,119,12,73,97,129,135,191,124,133,95,18,166,226,179,153,141,85,162,143,139,221,148,33,181,120,34,173,23,198,239,200,219,119,118,76,39,29,133,158,157,253,157,124,86,240,62,49,193,111,66,216,127,33,146,133,112,14,36,104,35,30,157,147,223,116,249,232,30,7,40,168,21,129,66,188,112,52,104,25,118,59,222,126,252,136,37,218,73,131,203,88,121,191,13,146,203,206,252,89,148,248,54,49,99,183,65,82,70,217,255,139,111,183,185,17,13,166,82,167,90,64,107,156,96,47,125,16,197,105,96,226,243,107,7,149,165,77,158,146,21,248,50,105,55,251,161,121,46,30,231,130,226,96,198,240,76,10,27,3,107,190,133,217,21,52,233,157,246,202,205,194,36,148,56,37,64,12,249,150,116,35,27,42,86,72,183,201,237,84,85,17,6,222,47,207,178,31,144,88,165,173,126,208,120,8,53,160,79,249,229,104,97,195,62,47,87,192,109,112,101,86,79,65,234,104,43,29,123,58,236,67,4,235,56,3,212,233,212,100,5,118,161,200,146,177,52,64,170,129,220,141,185,227,1,113,131,87,24,141,225,114,89,200,166,27,41,241,49,161,92,65,97,244,97,203,178,121,147,205,202,229,172,210,86,222,39,59,151,179,169,195,4,173,199,255,83,19,142,171,78,117,59,144,239,0,247,54,201,73,22,179,20,220,119,214,110,87,91,174,135,28,203,198,83,76,229,249,148,105,227,136,122,204,138,126,92,64,196,171,125,141,1,5,216,149,40,39,201,172,33,81,38,146,125,144,75,208,185,219,126,244,203,217,97,169,192,175,163,134,43,97,182,93,209,193,67,66,237,29,64,105,14,120,94,225,158,43,64,210,226,160,125,216,21,70,254,50,43,243,28,31,89,231,127,91,212,210,17,110,175,126,249,16,63,238,18,112,143,240,200,173,158,18,107,75,180,91,209,117,238,95,67,174,133,131,242,238,27,250,17,84,3,210,125,219,114,18,230,7,54,215,147,156,137,25,126,114,57,241,179,35,136,81,95,148,191,210,203,41,159,116,14,156,165,254,98,12,104,146,220,56,67,209,10,38,149,153,243,105,134,137,197,200,98,78,182,195,236,121,106,114,179,119,81,4,214,191,107,97,215,207,135,18,228,155,165,70,47,40,92,215,246,31,164,59,98,170,91,76,159,77,142,103,234,139,115,231,162,194,208,43,50,196,185,238,173,34,28,158,33,127,232,223,175,34,143,145,149,182,37,152,108,201,215,83,249,37,178,183,28,84,229,53,240,101,244,44,207,103,221,238,10,103,153,34,138,175,147,155,71,139,110,135,89,49,126,157,55,179,0,6,171,183,48,242,11,230,178,126,79,108,83,30,73,196,100,194,23,134,140,232,61,76,238,46,32,105,178,179,170,194,20,115,7,59,230,247,226,224,139,67,137,241,150,130,193,220,79,44,50,177,81,8,85,202,10,200,105,226,196,113,126,164,139,6,189,244,126,251,190,210,221,81,61,16,225,244,241,77,182,14,201,35,182,112,40,2,130,6,190,155,45,25,79,119,148,25,165,238,190,100,249,84,143,20,201,181,218,255,34,162,96,11,224,156,71,197,20,99,130,158,106,63,35,126,11,71,203,249,232,70,65,102,220,7,255,56,252,240,64,56,227,56,255,186,250,251,195,177,210,95,233,109,109,109,216,113,147,96,174,72,97,222,92,203,216,224,5,52,164,56,214,84,122,27,86,105,237,235,81,87,5,86,222,60,120,247,3,86,137,210,35,11,196,243,196,175,2,142,58,36,193,113,96,154,95,102,153,183,171,49,8,34,50,95,208,195,91,202,182,43,151,253,55,224,168,69,72,215,31,236,41,114,188,195,215,30,226,82,115,244,123,206,95,200,245,204,247,246,207,38,140,207,98,8,116,221,235,108,255,186,146,68,231,226,16,22,80,247,7,206,94,250,127,189,186,151,109,18,227,34,68,86,186,141,124,171,183,149,154,110,233,11,25,56,249,85,46,137,111,108,87,83,185,77,19,46,58,135,214,58,115,27,116,87,181,255,122,109,195,216,122,127,174,1,168,33,135,128,65,19,43,31,253,127,6,76,126,187,26,173,34,102,223,92,42,47,136,132,128,127,9,164,27,194,70,152,126,192,194,2,55,145,132,185,42,238,218,239,126,232,221,103,130,69,90,220,150,79,193,195,38,106,241,55,228,167,225,48,65,101,171,120,235,30,180,50,211,145,60,255,182,143,103,96,78,106,195,123,141,145,36,78,226,213,224,196,165,46,176,233,8,143,89,202,43,14,62,231,53,15,114,94,113,50,159,168,206,228,6,24,183,91,130,12,151,141,242,162,44,15,12,31,138,182,210,243,29,7,236,127,100,205,69,79,212,8,175,21,199,61,200,15,192,113,159,104,167,85,204,228,81,23,150,198,161,200,133,194,236,72,200,237,226,171,187,188,217,106,21,19,207,61,126,126,63,121,228,20,145,189,249,200,138,72,167,211,129,123,81,103,138,52,187,7,58,175,28,21,209,233,249,137,4,159,114,17,208,142,189,93,180,44,248,43,135,215,151,26,184,78,227,118,154,219,90,71,84,141,101,130,89,221,164,156,155,110,247,169,152,159,13,153,82,53,120,212,226,127,206,223,180,221,121,217,51,53,110,193,104,109,136,145,13,154,164,138,25,123,43,127,6,255,237,254,22,168,240,59,130,104,70,48,251,14,115,238,85,176,110,79,186,90,225,150,48,217,87,19,79,38,216,181,50,164,100,186,133,229,174,14,34,32,111,102,143,3,30,42,115,226,235,93,3,230,2,66,34,48,128,238,13,103,14,62,27,113,117,186,149,139,89,161,138,252,253,196,164,4,177,174,134,14,195,50,151,222,197,64,124,124,69,123,190,141,247,219,1,33,68,43,252,240,34,67,2,107,61,75,61,180,63,250,244,27,40,29,77,192,45,192,190,213,149,107,13,175,217,34,106,100,127,156,177,27,225,42,66,199,90,240,45,188,153,48,42,138,241,164,106,168,163,206,255,63,71,115,251,73,141,246,245,124,92,134,140,210,219,47,216,133,188,17,242,46,247,244,39,161,94,162,63,153,41,144,211,67,164,181,235,58,25,224,5,130,190,68,229,123,235,34,4,141,109,120,74,131,250,66,94,186,33,109,68,153,147,200,247,121,135,91,153,118,83,47,252,212,91,50,238,101,49,203,124,63,39,48,101,160,213,87,224,145,109,126,194,29,163,157,123,179,116,34,192,248,171,97,53,87,253,100,147,14,93,42,173,58,144,162,143,85,229,92,185,220,158,227,85,186,105,76,180,248,140,86,86,94,183,225,49,99,222,58,39,156,51,18,90,192,2,67,45,110,185,73,69,5,177,167,173,215,230,251,89,49,158,203,182,38,48,255,128,174,57,194,203,166,168,178,7,71,85,49,197,48,114,78,157,202,145,193,142,101,158,48,164,166,112,251,31,207,46,245,129,62,46,53,100,106,253,175,177,216,177,167],
        "url_key":
        {
            "seq": 2,
            "peer_key": "0rD95mGwiZznl34bejOzwEOK+PZZZnOeLoKzw794TmSM=",
            "type": "base_x_public"
        }
    }
}
```

#### Token

- Source page: `Maintenance/SystemUpgrade/Token.html`
- Purpose: This API is used to get system upgrade Token.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/SystemUpgrade/Token
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{
        "file_name":"N7XXX_V230625V230625V230625V230701V230701V230701V230625V230625.sw",
        "file_size":74328284,
        "upgrade_head":[220,39,110,4,32,2,0,0,125,15,88,1,187,40,116,7,57,218,176,153,74,21,0,172,191,216,204,132,183,161,245,241,131,212,116,145,237,107,37,83,117,253,79,245,70,166,0,98,57,132,230,96,192,170,31,171,170,119,197,49,224,159,237,59,68,132,58,64,207,3,113,130,18,122,63,232,12,58,32,96,24,3,195,186,116,97,1,58,68,188,175,216,209,5,67,125,235,117,46,208,211,66,224,204,25,198,32,103,24,174,163,60,71,110,121,186,162,20,109,46,188,232,226,186,228,188,201,227,254,160,201,97,143,208,42,47,144,237,100,157,107,119,142,158,166,9,89,133,77,163,55,200,104,62,188,122,224,240,88,170,31,178,117,49,228,3,96,231,102,241,51,193,127,176,215,198,218,16,45,164,143,78,223,209,144,160,91,251,51,186,85,68,159,234,209,88,151,136,8,255,202,71,72,56,87,19,94,218,30,60,180,12,144,248,161,111,223,2,187,181,188,241,108,78,18,64,221,152,200,158,192,33,218,203,241,90,186,155,255,233,181,255,104,230,166,115,69,223,35,101,255,15,87,53,41,84,161,66,180,246,10,205,249,121,78,55,88,88,88,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,109,86,147,204,1,0,0,0,204,0,0,0,0,0,0,0,196,0,0,0,8,0,0,0,2,0,0,0,86,50,51,48,54,50,53,0,3,0,0,0,86,50,51,48,54,50,53,0,4,0,0,0,86,50,51,48,54,50,53,0,5,0,0,0,86,50,51,48,55,48,49,0,6,0,0,0,86,50,51,48,55,48,49,0,7,0,0,0,86,50,51,48,55,48,49,0,11,0,0,0,86,50,51,48,54,50,53,0,12,0,0,0,86,50,51,48,54,50,53,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,70,30,16,114,252,150,59,22,155,67,56,37,171,172,67,211,206,219,231,92,106,154,226,87,34,19,0,253,199,225,202,91,182,160,106,100,62,243,118,123,11,29,214,254,45,249,151,36,40,255,98,89,157,108,189,249,71,155,142,170,1,166,18,141,161,154,0,46,229,115,207,169,82,57,219,201,95,128,179,104,63,232,170,41,175,194,92,189,2,120,55,0,0,121,122,228,6,131,220,198,146,151,101,141,68,84,110,188,50,124,36,244,101,160,129,83,107,27,75,154,24,52,146,183,152,9,112,119,80,21,99,83,24,63,46,64,159,52,40,236,204,48,197,151,254,155,103,159,126,175,161,120,243,59,25,98,229,212,3,45,6,218,208,66,2,217,217,18,250,157,240,157,45,222,243,49,211,165,204,193,191,225,87,7,147,196,247,235,178,29,68,166,225,175,187,78,123,203,5,127,77,237,52,204,176,168,172,252,98,116,158,230,76,77,23,255,194,159,57,221,34,38,176,8,146,49,40,80,201,124,47,63,228,148,32,70,3,112,62,216,44,13,114,132,180,51,81,230,242,16,116,0,246,178,236,123,166,244,11,184,74,78,177,90,181,186,244,66,253,112,37,139,89,92,179,190,7,137,237,191,73,193,176,244,254,114,100,128,64,253,245,58,208,169,36,146,209,73,175,59,196,153,185,141,49,26,233,154,150,79,173,58,245,15,150,87,88,12,27,201,33,105,120,4,184,101,78,146,61,9,210,253,63,119,174,130,219,219,36,97,4,155,1,128,125,189,170,119,197,211,200,166,105,70,48,113,173,180,126,237,150,184,110,71,87,113,21,104,141,197,164,202,224,253,237,15,76,12,210,238,191,69,9,198,24,208,233,40,238,207,26,161,41,129,51,203,24,222,167,147,32,58,102,16,144,137,51,111,207,216,163,115,132,242,240,20,177,97,86,185,128,250,21,98,91,97,124,201,107,89,215,150,72,60,56,251,135,115,222,55,196,183,36,192,75,72,108,130,70,97,170,69,116,142,131,78,85,12,182,139,15,150,148,241,77,242,222,53,230,36,220,115,124,19,100,223,226,13,104,56,61,126,87,29,137,106,179,71,187,179,103,244,71,166,5,172,119,200,64,104,254,44,82,30,156,185,113,71,44,61,112,55,122,106,162,143,176,178,109,149,99,113,158,50,37,222,84,227,226,253,73,94,174,53,205,97,148,141,118,108,252,60,235,158,147,70,81,85,118,89,163,22,145,218,238,205,205,25,141,104,16,36,100,76,217,205,141,112,34,85,149,155,137,203,231,186,139,137,171,124,154,3,25,63,34,225,246,209,145,69,96,3,94,124,120,36,178,194,193,153,192,95,12,61,14,73,171,212,8,156,68,3,56,191,114,162,12,35,4,23,190,8,221,138,145,105,89,112,153,63,215,76,169,102,87,159,158,177,11,114,97,136,84,4,92,178,211,21,209,141,35,52,17,179,255,167,86,77,148,29,128,53,94,74,70,89,19,107,146,138,50,246,151,116,45,92,222,107,181,19,149,129,245,19,133,30,10,80,62,129,149,228,242,83,89,245,79,204,143,11,11,71,63,211,28,42,178,43,52,225,9,157,174,162,239,238,245,122,253,91,231,206,162,231,217,204,246,12,254,31,163,175,132,150,33,78,81,224,65,53,88,18,185,132,167,171,52,198,246,108,195,197,223,185,182,41,27,151,1,161,193,88,169,110,151,104,143,29,159,179,131,112,5,150,21,150,203,211,181,29,88,4,96,124,106,240,213,224,228,159,209,195,2,151,242,242,17,85,238,36,196,174,76,115,231,123,116,237,212,213,106,199,229,134,235,196,244,221,32,146,87,235,229,160,195,182,209,89,128,75,137,134,7,205,147,206,219,171,5,195,27,215,88,230,156,205,241,120,182,2,98,88,65,110,40,34,42,79,191,222,25,61,37,119,195,168,203,150,255,107,247,150,123,54,185,156,205,5,26,74,114,241,28,26,214,72,100,162,52,64,114,240,14,255,12,205,175,182,105,242,26,34,188,195,36,230,246,248,3,42,106,162,130,176,106,96,94,5,161,148,117,235,213,89,202,124,218,80,241,58,189,200,157,171,132,142,125,118,57,136,199,179,155,207,169,127,213,229,75,207,141,43,208,222,146,49,180,53,210,66,176,224,112,119,12,73,97,129,135,191,124,133,95,18,166,226,179,153,141,85,162,143,139,221,148,33,181,120,34,173,23,198,239,200,219,119,118,76,39,29,133,158,157,253,157,124,86,240,62,49,193,111,66,216,127,33,146,133,112,14,36,104,35,30,157,147,223,116,249,232,30,7,40,168,21,129,66,188,112,52,104,25,118,59,222,126,252,136,37,218,73,131,203,88,121,191,13,146,203,206,252,89,148,248,54,49,99,183,65,82,70,217,255,139,111,183,185,17,13,166,82,167,90,64,107,156,96,47,125,16,197,105,96,226,243,107,7,149,165,77,158,146,21,248,50,105,55,251,161,121,46,30,231,130,226,96,198,240,76,10,27,3,107,190,133,217,21,52,233,157,246,202,205,194,36,148,56,37,64,12,249,150,116,35,27,42,86,72,183,201,237,84,85,17,6,222,47,207,178,31,144,88,165,173,126,208,120,8,53,160,79,249,229,104,97,195,62,47,87,192,109,112,101,86,79,65,234,104,43,29,123,58,236,67,4,235,56,3,212,233,212,100,5,118,161,200,146,177,52,64,170,129,220,141,185,227,1,113,131,87,24,141,225,114,89,200,166,27,41,241,49,161,92,65,97,244,97,203,178,121,147,205,202,229,172,210,86,222,39,59,151,179,169,195,4,173,199,255,83,19,142,171,78,117,59,144,239,0,247,54,201,73,22,179,20,220,119,214,110,87,91,174,135,28,203,198,83,76,229,249,148,105,227,136,122,204,138,126,92,64,196,171,125,141,1,5,216,149,40,39,201,172,33,81,38,146,125,144,75,208,185,219,126,244,203,217,97,169,192,175,163,134,43,97,182,93,209,193,67,66,237,29,64,105,14,120,94,225,158,43,64,210,226,160,125,216,21,70,254,50,43,243,28,31,89,231,127,91,212,210,17,110,175,126,249,16,63,238,18,112,143,240,200,173,158,18,107,75,180,91,209,117,238,95,67,174,133,131,242,238,27,250,17,84,3,210,125,219,114,18,230,7,54,215,147,156,137,25,126,114,57,241,179,35,136,81,95,148,191,210,203,41,159,116,14,156,165,254,98,12,104,146,220,56,67,209,10,38,149,153,243,105,134,137,197,200,98,78,182,195,236,121,106,114,179,119,81,4,214,191,107,97,215,207,135,18,228,155,165,70,47,40,92,215,246,31,164,59,98,170,91,76,159,77,142,103,234,139,115,231,162,194,208,43,50,196,185,238,173,34,28,158,33,127,232,223,175,34,143,145,149,182,37,152,108,201,215,83,249,37,178,183,28,84,229,53,240,101,244,44,207,103,221,238,10,103,153,34,138,175,147,155,71,139,110,135,89,49,126,157,55,179,0,6,171,183,48,242,11,230,178,126,79,108,83,30,73,196,100,194,23,134,140,232,61,76,238,46,32,105,178,179,170,194,20,115,7,59,230,247,226,224,139,67,137,241,150,130,193,220,79,44,50,177,81,8,85,202,10,200,105,226,196,113,126,164,139,6,189,244,126,251,190,210,221,81,61,16,225,244,241,77,182,14,201,35,182,112,40,2,130,6,190,155,45,25,79,119,148,25,165,238,190,100,249,84,143,20,201,181,218,255,34,162,96,11,224,156,71,197,20,99,130,158,106,63,35,126,11,71,203,249,232,70,65,102,220,7,255,56,252,240,64,56,227,56,255,186,250,251,195,177,210,95,233,109,109,109,216,113,147,96,174,72,97,222,92,203,216,224,5,52,164,56,214,84,122,27,86,105,237,235,81,87,5,86,222,60,120,247,3,86,137,210,35,11,196,243,196,175,2,142,58,36,193,113,96,154,95,102,153,183,171,49,8,34,50,95,208,195,91,202,182,43,151,253,55,224,168,69,72,215,31,236,41,114,188,195,215,30,226,82,115,244,123,206,95,200,245,204,247,246,207,38,140,207,98,8,116,221,235,108,255,186,146,68,231,226,16,22,80,247,7,206,94,250,127,189,186,151,109,18,227,34,68,86,186,141,124,171,183,149,154,110,233,11,25,56,249,85,46,137,111,108,87,83,185,77,19,46,58,135,214,58,115,27,116,87,181,255,122,109,195,216,122,127,174,1,168,33,135,128,65,19,43,31,253,127,6,76,126,187,26,173,34,102,223,92,42,47,136,132,128,127,9,164,27,194,70,152,126,192,194,2,55,145,132,185,42,238,218,239,126,232,221,103,130,69,90,220,150,79,193,195,38,106,241,55,228,167,225,48,65,101,171,120,235,30,180,50,211,145,60,255,182,143,103,96,78,106,195,123,141,145,36,78,226,213,224,196,165,46,176,233,8,143,89,202,43,14,62,231,53,15,114,94,113,50,159,168,206,228,6,24,183,91,130,12,151,141,242,162,44,15,12,31,138,182,210,243,29,7,236,127,100,205,69,79,212,8,175,21,199,61,200,15,192,113,159,104,167,85,204,228,81,23,150,198,161,200,133,194,236,72,200,237,226,171,187,188,217,106,21,19,207,61,126,126,63,121,228,20,145,189,249,200,138,72,167,211,129,123,81,103,138,52,187,7,58,175,28,21,209,233,249,137,4,159,114,17,208,142,189,93,180,44,248,43,135,215,151,26,184,78,227,118,154,219,90,71,84,141,101,130,89,221,164,156,155,110,247,169,152,159,13,153,82,53,120,212,226,127,206,223,180,221,121,217,51,53,110,193,104,109,136,145,13,154,164,138,25,123,43,127,6,255,237,254,22,168,240,59,130,104,70,48,251,14,115,238,85,176,110,79,186,90,225,150,48,217,87,19,79,38,216,181,50,164,100,186,133,229,174,14,34,32,111,102,143,3,30,42,115,226,235,93,3,230,2,66,34,48,128,238,13,103,14,62,27,113,117,186,149,139,89,161,138,252,253,196,164,4,177,174,134,14,195,50,151,222,197,64,124,124,69,123,190,141,247,219,1,33,68,43,252,240,34,67,2,107,61,75,61,180,63,250,244,27,40,29,77,192,45,192,190,213,149,107,13,175,217,34,106,100,127,156,177,27,225,42,66,199,90,240,45,188,153,48,42,138,241,164,106,168,163,206,255,63,71,115,251,73,141,246,245,124,92,134,140,210,219,47,216,133,188,17,242,46,247,244,39,161,94,162,63,153,41,144,211,67,164,181,235,58,25,224,5,130,190,68,229,123,235,34,4,141,109,120,74,131,250,66,94,186,33,109,68,153,147,200,247,121,135,91,153,118,83,47,252,212,91,50,238,101,49,203,124,63,39,48,101,160,213,87,224,145,109,126,194,29,163,157,123,179,116,34,192,248,171,97,53,87,253,100,147,14,93,42,173,58,144,162,143,85,229,92,185,220,158,227,85,186,105,76,180,248,140,86,86,94,183,225,49,99,222,58,39,156,51,18,90,192,2,67,45,110,185,73,69,5,177,167,173,215,230,251,89,49,158,203,182,38,48,255,128,174,57,194,203,166,168,178,7,71,85,49,197,48,114,78,157,202,145,193,142,101,158,48,164,166,112,251,31,207,46,245,129,62,46,53,100,106,253,175,177,216,177,167],
        "base_secondary_authentication":{
            "seq":2,
            "cipher":"FWRsfpB05p/NfdTleipoBR1d06/dZA2xO8cDJiF4CYM="
        }
    }
}
```

#### Upgrade

- Source page: `Maintenance/SystemUpgrade/Upgrade.html`
- Purpose: This API is used to upgrade system.
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/SystemUpgrade/Upgrade
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{
    }
}
```

#### VersionCheck

- Source page: `Maintenance/SystemUpgrade/VersionCheck.html`
- Purpose: This API is used to check for upgrade.(NVR needs to verify the version information in the ftp and http upgrade configuration files of IPC)
- Endpoint:
```http
POST http://000.00.00.000/API/Maintenance/SystemUpgrade/VersionCheck
```
- Request Body (JSON):
```json
{
    "data": {
        "FirewareVersion": "V30.85.8.2.4_231030",
        "FirewarePack": "CH529N_F128M_SF_ENU_V30.85.8.2.4_231030_08d1defe_W.sw",
        "url_key": {
            "type": "base_x_public",
            "peer_key": "0VSd/xFlbwJk8LnAuLk4VxTEVYy0kQrp5csFzL3BKryU=",
            "seq": 0
        }
    },
    "version": "1.0"
}
```

## MutexParam

### Root

#### MutexParam

- Source page: `MutexParam/API.html`
- Endpoint:
```http
POST http://000.00.00.000/API/MutexParam/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `MutexParam/Get.html`
- Endpoint:
```http
POST http://000.00.00.000/API/MutexParam/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

## Nerwork

### DDNS

#### DDNS

- Source page: `Nerwork/DDNS/API.html`
- Purpose: This API is used for get or set or test DDNS parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/DDNS/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Nerwork/DDNS/Get.html`
- Purpose: This API is used to get parameter for Network>DDNS.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/DDNS/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `Nerwork/DDNS/Range.html`
- Purpose: This API is used to get the parameter range of Network > DDNS.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/DDNS/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Nerwork/DDNS/Set.html`
- Purpose: This API is used to set parameter for Network > DDNS.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/DDNS/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "ddns_enable": true,
        "server": "NO_IP",
        "domain": "172.16.11.333",
        "username": "admin",
        "password_empty": false,
        "api_key_empty": true,
        "test_befault_save": false,
        "base_enc_password": {
            "seq": 0,
            "peer_key": "0mxizZ01CLypE9BhtfCNXAAwrpLR8W3wN95GKLSqpLEg=",
            "cipher": "0bCgObu9WoTP6k5pSpSGL98RBG2WK6T5Osmctk6BGxbE5e/KG"
        }
    }
}
```

#### Test

- Source page: `Nerwork/DDNS/Test.html`
- Purpose: This API is used to test parameter for Network > DDNS.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/DDNS/Test
```
- Request Body (JSON):
```json
{
  "version": "1.0",
    "data": {
        "ddns_enable": true,
        "server": "NO_IP",
        "domain": "172.16.11.333",
        "username": "admin",
        "password_empty": false,
        "api_key_empty": true,
        "test_befault_save": false,
        "base_enc_password": {
            "seq": 0,
            "peer_key": "0xODk3zoBTV+3MLNIjTSdV+GYzi3f38bH2UFX59Nk1R0=",
            "cipher": "0EmzlXN55rYmHMFN54IQTc/lYQrzp/0x2JT12Dbw1nbQN2O1v"
        }
    }
}
```

### Email

#### Email

- Source page: `Nerwork/Email/API.html`
- Purpose: This API is used for get or set or test Email parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Email/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Nerwork/Email/Get.html`
- Purpose: This API is used to get parameter for Network > Email.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Email/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
}
```

#### Range

- Source page: `Nerwork/Email/Range.html`
- Purpose: This API is used to get the parameter range of Network > Email.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Email/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Nerwork/Email/Set.html`
- Purpose: This API is used to set parameter for Network > Email.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Email/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "email_enable":true,
        "encryption":"Auto",
        "smtp_port":25,
        "smtp_server":"aaa",
        "username":"aaa",
        "password_empty":false,
        "sender":"aaaaa",
        "recvemail":
        {
            "recvemail_1":"aaaaa@qq.com",
            "recvemail_2":"aaaaa@qq.com",
            "recvemail_3":"aaaaa@qq.com"},
            "interval_time":3,
            "report_button":
            {
                "report_button_1":"send_device_report"
            }
        }
}
```

#### Test

- Source page: `Nerwork/Email/Test.html`
- Purpose: This API is used to test parameter for Network > Email.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Email/Test
```
- Request Body (JSON):
```json
{
    "data": {
        "email_enable": false,
        "encryption": "AUTO",
        "smtp_port": 25,
        "smtp_server": "smtp163.com",
        "username": "123456@qq.com ",
        "password": "321",
        "sender": "123456@qq.com",
        "recvemail_1": "654321@qq.com ",
        "recvemail_2": "",
        "recvemail_3": "",
        "interval_time": 3,
        "test_id": 3,
        "email_test_Flag":"start"
    }
}
```

### FTP

#### FTP

- Source page: `Nerwork/FTP/API.html`
- Purpose: This API is used for get or set or test FTP parameters
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Ftp/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Nerwork/FTP/Get.html`
- Purpose: This API is used to get parameter for Network > FTP .
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Ftp/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Range

- Source page: `Nerwork/FTP/Range.html`
- Purpose: This API is used to get the parameter range of Network > FTP.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Ftp/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Set

- Source page: `Nerwork/FTP/Set.html`
- Purpose: This API is used to set parameter for Network > FTP.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Ftp/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "ftp_enable":true,
        "server_ip":"aaa",
        "port":21,
        "username":"aaa",
        "password_empty":true,
        "picture_quality":"Higher",
        "video_stream_type":"Substream",
        "max_package_interval":30,
        "directory_name":"aaa",
        "base_enc_password":
        {
            "seq":0,
            "peer_key":"0fvTpiCxu35TY5Vn8vR1Ng/MB4rFf46Rj9/Tp+LFNRGU=",
            "cipher":"0cxEOj04QQA/8cMDCvYlhSCtsCPlL3fJkFyaO1ULXGA=="
        }
    }
}
```

#### Test

- Source page: `Nerwork/FTP/Test.html`
- Purpose: This API is used to test whether the FTP server is connected.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Ftp/Test
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "ftp_enable":true,
        "server_ip":"aaa",
        "port":21,
        "username":"aaa",
        "password_empty":false,
        "picture_quality":"Higher",
        "video_stream_type":"Substream",
        "max_package_interval":30,
        "directory_name":"aaa"
    }
}
```

### GBT28181

#### GBT28181

- Source page: `Nerwork/GBT28181/API.html`
- Purpose: This API is used to get or set or test GB/T28181 parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/T28181/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Nerwork/GBT28181/Get.html`
- Purpose: This API is used to get parameter for Network > GBT28181 .
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/T28181/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `Nerwork/GBT28181/Range.html`
- Purpose: This API is used to get the parameter range of Network > GBT28181.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/T28181/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Nerwork/GBT28181/Set.html`
- Purpose: This API is used to set parameter for Network > GBT28181.
- Endpoint:
```http
POST http://000.00.00.000/API/ NetworkConfig/T28181/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "server_port": 5061,
        "local_port": 5060,
        "stream_port": 55550,
        "heart_beat_time": 60,
        "expires": 3600,
        "enable_flag": true,
        "max_timeouts": 3,
        "stream_type": "Substream",
        "link_status": "GB28181_close",
        "server_ip": "172.16.8.15",
        "server_id": "51000000992000000001",
        "device_id": "34020000001340000001",
        "password_empty": true,
        "device_name": "IPC",
        "server_domain": "32050",
        "channel_nvr_id": [{"channel_id": "34020000001340000001"}],
        "enc_password": {
            "seq": 0,
            "peer_key": "0SaWizhlOpa0wQRqrlRMlkaeISft+e7O65RZpQSqbbhM=",
            "cipher": "0uWSr9VAP9/tos+bFguJw2qggJDEncuD/ryv+pz2aRw=="
        }
    }
}
```

### HTTPS

#### HTTPS

- Source page: `Nerwork/HTTPS/API.html`
- Purpose: This API is used to get or set HTTPS parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/https/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Nerwork/HTTPS/Get.html`
- Purpose: This API is used to get Network > HTTPS parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/https/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Range

- Source page: `Nerwork/HTTPS/Range.html`
- Purpose: This API is used to get the Network > HTTPS parameter range.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/https/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Set

- Source page: `Nerwork/HTTPS/Set.html`
- Purpose: This API is used to set Network > HTTPS parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/https/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "https_enable":true,
        "file_type":"Default",
        "file_exist":0,
        "operate":"Switch"
    }
}
```

### IEEE8021x

#### IEEE8021x

- Source page: `Nerwork/IEEE8021x/API.html`
- Purpose: This API is used for get or set IEEE8021x parameters.
- Endpoint:
```http
POST/API/NetworkConfig/IEEE8021x/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Nerwork/IEEE8021x/Get.html`
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/IEEE8021x/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Range

- Source page: `Nerwork/IEEE8021x/Range.html`
- Purpose: This API is used to get the parameter range of Network > IEEE8021x .
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/IEEE8021x/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Set

- Source page: `Nerwork/IEEE8021x/Set.html`
- Purpose: This API is used to set parameter for Network > IEEE8021x.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/IEEE8021x/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "ieee_enable": true,
        "authentication_type": "EAP-MD5",
        "username": "test",
        "password_empty": false,
        "authentication": {
            "client_certificate_server_certificate": {
                "install_button": true,
                "delete_button": false,
                "private_key_password": "",
                "private_key_password_empty": true
            },
            "client_passwd_auth_server_certificate": {
                "password": "",
                "password_empty": false,
                "install_button": true,
                "delete_button": false
            },
            "client_passwd_auth_only": {}
        },
        "base_enc_password": {
            "seq": 0,
            "peer_key": "0niVaQ47ri7+RhWeEISnYXJ1M27j7SYnxb8msT7AcMzw=",
            "cipher": "0Vtyz03DVcoD7dpfwgpEaDrPPTG2YCWOAO2pTnJOL04UbPlyMwHY="
        }
    }
}
```

### IP Filter

#### IP Filter

- Source page: `Nerwork/IP Filter/API.html`
- Purpose: This API is used to get or set IP filter parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/IPFilter/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Nerwork/IP Filter/Get.html`
- Purpose: This API is used to obtain Network > IP Filter parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/IPFilter/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Range

- Source page: `Nerwork/IP Filter/Range.html`
- Purpose: This API is used to obtain Network > IP Filter parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/IPFilter/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Set

- Source page: `Nerwork/IP Filter/Set.html`
- Purpose: This API is used to set Network > IP Filter parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/IPFilter/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "enable":true,
        "choose":"Whitelist",
        "restricted_type":"Whitelist",
        "whitelist":[
            {
                "ip_type":"Ipv4",
                "start_address":"192.193.1.223",
                "end_address":"192.193.1.223"
            }
        ],
        "blacklist":[]
    }
}
```

### ipv6

#### ipv6

- Source page: `Nerwork/ipv6/API.html`
- Purpose: This API is used for get or set ipv6 parameters
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Ipv6/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Nerwork/ipv6/Get.html`
- Purpose: This API is used to get parameter for Network > ipv6.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/ipv6/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Range

- Source page: `Nerwork/ipv6/Range.html`
- Purpose: This API is used to get the parameter range of Network > ipv6.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/ipv6/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Set

- Source page: `Nerwork/ipv6/Set.html`
- Purpose: This API is used to set parameter for Network > ipv6.
- Endpoint:
```http
HTTP/1.1 200 OK
Content-Type: application/json
```
- Request Body (JSON):
```json
{
    "data": {
        "prefixlen": 64,
        "local_ipv6_addr": "fe80::223:63ff:fe0a:901b",
        "global_ipv6_addr": "fe80::223:63ff:fe0a:901b"
    }
}
```

### Network Configuration / Network Base

#### Network Base

- Source page: `Nerwork/Network Configuration/Network Base/API.html`
- Purpose: This API is used for get or set device network interfaces.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/NetBase/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Nerwork/Network Configuration/Network Base/Get.html`
- Purpose: This API is used to get parameter for Network > Network Configuration > Network Base.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/NetBase/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Range

- Source page: `Nerwork/Network Configuration/Network Base/Range.html`
- Purpose: This API is used to get the parameter range of Network > Network Configuration > Network Base.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/NetBase/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"page_type": "net_general"}
}
```

#### Set

- Source page: `Nerwork/Network Configuration/Network Base/Set.html`
- Purpose: This API is used to set parameter for Network > Network Configuration > Network Base.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/NetBase/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "page_type": "net_general",
        "wan": {
            "dhcp": false,
            "ip_address": "172.016.010.169",
            "subnet_mask": "255.255.000.000",
            "gateway": "172.016.008.001",
            "ipv6_address": "fe80::5ef2:7ff:fe49:3141",
            "ipv6_prefixlen": 64,
            "ipv6_gateway": "fe80::/64",
            "dns1": "172.018.001.222",
            "dns2": "008.008.008.008",
            "dhcp_enable": true
        },
        "web_compatibility_mode": false,
        "lan": {
            "poedhcp": true,
            "ip_address": "010.010.025.100",
            "subnet_mask": "255.255.000.000"
        },
        "video_encrypt_transfer": []
    }
}
```

### Network Configuration / WLAN

#### WLANScan

- Source page: `Nerwork/Network Configuration/WLAN/API.html`
- Purpose: This API is used for get or set WIFI parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/ScanWlan/{Action1}
POST http://000.00.00.000/API/NetworkConfig/MacthWiFiType/{Action2}
POST http://000.00.00.000/API/APNetworkCfg/{Action3}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### join

- Source page: `Nerwork/Network Configuration/WLAN/join.html`
- Purpose: This API is used to add wifi parameter for Network > WLANScan.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/ScanWlan/Join
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "ssid": "TPXXX",
        "base_enc_password": {
            "seq": 0,
            "peer_key": "06AX8xRt+bAfD+jV8UpMl+zIcbNkakYIFi3X7YlBWhgs=",
            "cipher": "0WwwRvSgRDydPvrCqmbZrHRcpjsEYC+TbW8tDVNzQPvP6OvHZ"
        }
    }
}
```

#### Set

- Source page: `Nerwork/Network Configuration/WLAN/MacthWiFiTypeSet.html`
- Purpose: This API is used to set wifi type parameter for Network > WLANScan.
- Endpoint:
```http
POST http://000.00.00.000/API/APNetworkCfg/WifiStaParam/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data":
    {
        "restart_to_match_wifitype": false,
        "current_wifitype": 1
    }
}
```

#### Scan

- Source page: `Nerwork/Network Configuration/WLAN/Scan.html`
- Purpose: This API is used to get wifi list for Network > WLANScan.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/ScanWlan/Scan
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Set

- Source page: `Nerwork/Network Configuration/WLAN/WifiStaParamSet.html`
- Purpose: This API is used to set wifi AP parameter for Network > WLANScan.This API interface will only be registered and enabled in AP mode.
- Endpoint: Not explicitly documented in a request sample on this page.
- Request Body (JSON): No JSON request body sample was documented on this page.

### Onvif

#### Onvif

- Source page: `Nerwork/Onvif/API.html`
- Purpose: This API is used for get or set onvif parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Onvif/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Nerwork/Onvif/Get.html`
- Purpose: This API is used to get parameter for Network>Onvif.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Onvif/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Range

- Source page: `Nerwork/Onvif/Range.html`
- Purpose: This API is used to get the parameter range of Network > Onvif.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Onvif/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Set

- Source page: `Nerwork/Onvif/Set.html`
- Purpose: This API is used to set parameter for Network>Onvif.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Onvif/Set
```
```http
HTTP/1.1 200 OK
Content-Type: application/json
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "enable": true,
        "authentication": "Digest/WSSE",
        "protocol": "HTTP/HTTPS",
        "username": "admin",
        "password_empty": true,
        "base_enc_password": {
            "seq": 0,
            "peer_key": "0N4LDE7DDSoiCDMGeeQ4I+O0IXnfhyA4uene9qOPvbSs=",
            "cipher": "0ffNkxOJ7eSs6B18xbA35JJakUmjvL/oD/570IoNAYEvBDjhL"
        }
    }
}
```
```json
{
    "result":"success",
    "data":{}   
}
```

### Rtsp

#### Rtsp

- Source page: `Nerwork/Rtsp/API.html`
- Purpose: This API is used for get or set Rtsp parameters.
- Endpoint:
```http
POST/API/NetworkConfig/Rtsp/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Nerwork/Rtsp/Get.html`
- Purpose: This API is used to get parameter for Network>Rtsp .
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Rtsp/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Range

- Source page: `Nerwork/Rtsp/Range.html`
- Purpose: This API is used to get the parameter range of Network > Rtsp.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Rtsp/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Set

- Source page: `Nerwork/Rtsp/Set.html`
- Purpose: This API is used to set parameter for Network>Rtsp.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Rtsp/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "rtsp_enable": true,
        "rtsp_check_flag": true,
        "anonymous_login": false,
        "rtsp_url": "rtsp://IP:RtspPort/ch01/A",
        "ipeye_enable": true,
        "metadata_platform": "None"
    }
}
```

### snmp

#### snmp

- Source page: `Nerwork/snmp/API.html`
- Purpose: This API is used for get or set snmp parameters.
- Endpoint:
```http
POST/API/NetworkConfig/Snmp/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Nerwork/snmp/Get.html`
- Purpose: This API is used to get parameter for Network>snmp.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Snmp/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Range

- Source page: `Nerwork/snmp/Range.html`
- Purpose: This API is used to get the parameter range of Network > snmp.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Snmp/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Set

- Source page: `Nerwork/snmp/Set.html`
- Purpose: This API is used to set parameter for Network>snmp.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Snmp/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "snmp_enable": true,
        "snmp_versions": "V3",
        "snmp_port": 161,
        "read_community": "public",
        "write_community": "private",
        "trap_ipaddr": "127.0.0.1",
        "trap_port": 162,
        "authentication": {
            "readonly_user": {
                "username": "authOnlyUser",
                "authentication_type": "MD5",
                "authentication_password_empty": false,
                "encrypted_type": "CBC-DES",
                "encrypted_password_empty": false,
                "base_enc_authentication_password": {
                    "seq": 0,
                    "peer_key": "0D+VG/UsfUQuIknWk1L8Wg4G9HW9VjkKGStyaOdK68W4=",
                    "cipher": "0lA3HPPzyuk8h8+PSTXcgxAaGwf5K9k1w3U11CWtrOPwHaBy1"
                },
                "base_enc_encrypted_password": {
                    "seq": 0,
                    "peer_key": "0ZiA2CYOlj+8sZQTDIzO9G4myWMdg0h+Nozx3O/MBr0I=",
                    "cipher": "0oK0YB8zf6Wu3ryDoRuSW0lQt/69DCH+XagPWVUfMUfQwKeqoPXEoPN8="
                }
            },
            "readwrite_user": {
                "username": "authPrivUser",
                "authentication_type": "MD5",
                "authentication_password_empty": false,
                "encrypted_type": "CBC-DES",
                "encrypted_password_empty": false
            }
        }
    }
}
```

### Tuya

#### Tuya

- Source page: `Nerwork/Tuya/API.html`
- Purpose: This API is used for get or set tuya parameters.
- Endpoint:
```http
POST/API/NetworkConfig/Tuya/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Nerwork/Tuya/Get.html`
- Purpose: This API is used to get parameter for Network>Tuya.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Tuya/Get
```
- Request Body (JSON):
```json
{
    "version":"1.0"
}
```

#### Range

- Source page: `Nerwork/Tuya/Range.html`
- Purpose: This API is used to get the parameter range of Network > Tuya.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Tuya/Range
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":{}
}
```

#### Set

- Source page: `Nerwork/Tuya/Set.html`
- Purpose: This API is used to set parameter for Network>Tuya.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/Tuya/Set
```
- Request Body (JSON):
```json
{
    "version":"1.0",
    "data":
    {
        "enable":"true"
    }
}
```

### Voice Assistant

#### Voice Assistant

- Source page: `Nerwork/Voice Assistant/API.html`
- Purpose: This API is used for get or control voice assistant parameters.
- Endpoint:
```http
POST/API/NetworkConfig/VoiceAssistant/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Nerwork/Voice Assistant/Get.html`
- Purpose: This API is used to get parameter for Network>Voice Assistant.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/SMARTHOME/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"SmartHomePage": "Amazon"}
}
```

#### Range

- Source page: `Nerwork/Voice Assistant/Range.html`
- Purpose: This API is used to get the parameter range of Network > Voice Assistant.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/SMARTHOME/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"SmartHomePage": "Amazon"}
}
```

#### Control

- Source page: `Nerwork/Voice Assistant/Set.html`
- Purpose: This API is used to control Network>Voice Assistant.
- Endpoint:
```http
POST http://000.00.00.000/API/NetworkConfig/SMARTHOME/Control
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "BindEnable": true,
        "UserName": "xxxxx@qq.com",
        "ScreenStream": "Mainstream",
        "SmartHomePage": "Amazon",
        "operate": "Apply"
    }
}
```

## Push

### Push

#### Push

- Source page: `Push/Push/API.html`
- Purpose: This API is used for push messages.
- Endpoint:
```http
POST http://000.00.00.000/API/Push/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### GetToken

- Source page: `Push/Push/GetToken.html`
- Purpose: This API is used to obtain Token when pushing.
- Endpoint:
```http
POST http://000.00.00.000/API/Push/GetToken
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "Token":"f06214c1d9348dee11a513213c9a38d0b62c9ffd32d1c1b6f6485117d1f187b9"
    }
}
```

#### Query

- Source page: `Push/Push/Query.html`
- Purpose: This API is used to push query push parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/Push/Query
```
- Request Body (JSON):
```json
{
    "data": {
        "Token": "f06214c1d9348dee11a513213c9a38d0b62c9ffd32d1c1b6f6485117d1f187b9",
        "app_support_ai_notification_subscribe":true
    }
}
```

#### QueryDefault

- Source page: `Push/Push/QueryDefault.html`
- Purpose: This API is used to restore default push.
- Endpoint:
```http
POST http://000.00.00.000/API/Push/QueryDefault
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Get

- Source page: `Push/Push/Subscribe.html`
- Purpose: This API is used for push subscriptions.
- Endpoint:
```http
POST http://000.00.00.000/API/Push/Subscribe
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "Filter": {
            "AD": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            },
            "AiFaceDetection": {
            "Group": [
                {
                "Channel": [0,1,2,3,4,5,6,7,8],
                "Name": "Allow List"
                },
                {
                "Channel": [0,1,2,3,4,5,6,7,8],
                "Name": "Block List"
                },
                {
                "Channel": [0,1,2,3,4,5,6,7,8],
                "Name": "Stranger"
                }
            ]
            },
            "AiHuman": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            },
            "AiVehicle": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            },
            "CC": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            },
            "CD": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            },
            "FD": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            },
            "Intrusion": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            },
            "IOAlarm": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            },
            "LCD": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            },
            "LPD": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            },
            "LPR": {
            "Group": [
                {
                "Channel": [0,1,2,3,4,5,6,7,8],
                "Name": "Allow List"
                },
                {
                "Channel": [0,1,2,3,4,5,6,7,8],
                "Name": "Block List"
                },
                {
                "Channel": [0,1,2,3,4,5,6,7,8],
                "Name": "Unknown"
                }
            ]
            },
            "Motion": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            },
            "PID": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            },
            "PIRAlarm": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            },
            "PD&VD": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            },
            "QD": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            },
            "RegionEntrance": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            },
            "RegionExiting": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            },
            "RSD": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            },
            "SD": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            },
            "SOD": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            },
            "StorageError": {},
            "StorageFull": {},
            "StorageNull": {},
            "StorageUnformatted": {},
            "VideoLoss": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            },
            "VT": {
            "Channel": [0,1,2,3,4,5,6,7,8]
            }
        },
        "Notification": {
            "notification_interval": 1,
            "notification_interval_switch": false
        },
        "MobileInfo":[
            {
                "Mobile": {
                "AppID": "com.RXCamView.push",
                "Language": "zh-Hans",
                "PushChannel": "APNS",
                "Token": "eyJhbGciOiJFUzI1NiIsImtpZCI6InJzdHM4Mjg1NWI4MmNmNDk0YWM5OWNiZGM4OTQ2YTQ0YWYxNyJ9.eyJhdWQiOlsicHNfZGVsIl0sIlgtc3ViIjp7IlRva2VuIjoiZjA2MjE0YzFkOTM0OGRlZTExYTUxMzIxM2M5YTM4ZDBiNjJjOWZmZDMyZDFjMWI2ZjY0ODUxMTdkMWYxODdiOSIsIlVVSUQiOiI2ZTMzMjJjMy01MjFmLTQ0OWItYjk0Yy00MjE5ZGJiOTIwMmMifX0.ec_DrzO6AYidvJytmKADN9iW4sy3LqHBMJj9QEVaySquqlby43Oe5UvtqrU0y0t6o8cno6ypX9v4vzp5QGRbZw"
                },
                "UUID": "7c42cecc-7989-43df-8baf-86065abffac0"
            }
        ]
    }
}
```

#### Unsubscribe

- Source page: `Push/Push/Unsubscribe.html`
- Purpose: This API is used to close push.
- Endpoint:
```http
POST http://000.00.00.000/API/Push/Unsubscribe
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "Token":"f06214c1d9348dee11a513213c9a38d0b62c9ffd32d1c1b6f6485117d1f187b9",
        "UUID": "7c42cecc-7989-43df-8baf-86065abffac0"
    }
}
```

### PushSubscribe

#### PushSubscribe

- Source page: `Push/PushSubscribe/API.html`
- Purpose: This API is used to get or set push subscriptions.
- Endpoint:
```http
POST http://000.00.00.000/API/PushSubscribe/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Push/PushSubscribe/Get.html`
- Purpose: This API is used to get push subscriptions.
- Endpoint:
```http
POST http://000.00.00.000/API/PushSubscribe/Get
```
- Request Body (JSON):
```json
{
    "data": {
        "app_support_ai_notification_subscribe":true
    }
}
```

#### Set

- Source page: `Push/PushSubscribe/Set.html`
- Purpose: This API is used to setup push subscriptions.
- Endpoint:
```http
POST http://000.00.00.000/API/PushSubscribe/Set
```
- Request Body (JSON):
```json
{
    "data": {
        "HddAlarm": {
            "Enabled": 1,
            "Type": 0
        },
        "IOAlarm": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "LowPower": {
            "ChnFlags": [
                255,
                0
            ]
        },
        "MotionAlarm": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "PIRAlarm": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "LCDAlarm": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "PIDAlarm": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "SODAlarm": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "PDAlarm": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "FDAlarm": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "CCAlarm": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "ADAlarm": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "CDAlarm": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "QDAlarm": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "LPDAlarm": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "RSDAlarm": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "VTAlarm": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "SDAlarm": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "VideoLoss": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "Human": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "Vehicle": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "IntrusionAlarm": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "RegionEntranceAlarm": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "RegionExitingAlarm": {
            "ChnFlags": [
                255,
                255
            ]
        },
        "FaceAlarm": {
            "Group": [
                {
                    "Id": 2,
                    "Name": "Allow List",
                    "ChnFlags": [
                        0,
                        0
                    ]
                },
                {
                    "Id": 3,
                    "Name": "Block List",
                    "ChnFlags": [
                        0,
                        0
                    ]
                }
            ]
        },
        "LPRAlarm": {
            "Group": [
                {
                    "Id": 5,
                    "Name": "Allow List",
                    "ChnFlags": [
                        0,
                        0
                    ]
                },
                {
                    "Id": 6,
                    "Name": "Block List",
                    "ChnFlags": [
                        0,
                        0
                    ]
                }
            ]
        }
    }
}
```

## Record

### Month Search

#### Month Search

- Source page: `Record/Month Search/API.html`
- Purpose: This API is used to get month playback data for a specified date.
- Endpoint:
```http
POST http://000.00.00.000/API/Playback/SearchMonth/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Record/Month Search/Get.html`
- Purpose: This API is used to get month playback data for a specified date.
- Endpoint:
```http
POST http://000.00.00.000/API/Playback/SearchMonth/Get
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"channel": [],
		"stream_type": "Substream",
		"start_date": "05/31/2023",
		"search_type": "Record"
	}
}
```

### Pic Playback

#### Pic Playback

- Source page: `Record/Pic Playback/API.html`
- Purpose: This API is used to get image information.
- Endpoint:
```http
POST http://000.00.00.000/API/Playback/Picture/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Record/Pic Playback/Get.html`
- Purpose: This API is used to get image information.
- Endpoint:
```http
POST http://000.00.00.000/API/Playback/Picture/Get
```
```http
POST http://000.00.00.000/API/Playback/Picture/Get
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"record_type_ex": [
			4294967295
		],
		"start_date": "06/29/2023",
		"start_time": "00:00:00",
		"end_date": "06/29/2023",
		"end_time": "23:59:59",
		"record_type": 524287,
		"channel": [
			"CH1",
			"CH2",
			"CH3",
			"CH4",
			"CH5",
			"CH6",
			"CH7",
			"CH8",
			"CH9",
			"CH10",
			"CH11",
			"CH12",
			"CH13",
			"CH14",
			"CH15",
			"CH16"
		],
		"pic_sort": 0
	}
}
```
```json
{
	"version": "1.0",
	"data": {
		"pic_info": "AQAAOQAAAABcAgAAAQAAAAAAAAAAAAAAAAQCAB0GFwAA0K4AKGECAEEAAAAAAAAA"
	}
}
```

### Playback Page

#### Playback Page

- Source page: `Record/Playback Page/API.html`
- Purpose: This API is used to get Playback page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/Playback/PlaybackPage/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Range

- Source page: `Record/Playback Page/Range.html`
- Purpose: This API is used to get parameter range for Record > Playback Page page.
- Endpoint:
```http
POST http://000.00.00.000/API/Playback/PlaybackPage/Range
```
- Request Body (JSON):
```json
{
	"version": "1.0"
}
```

### Playback rtsp url

#### Playback rtsp url

- Source page: `Record/Playback rtsp url/API.html`
- Purpose: This API is used to play playback videos.
- Endpoint:
```http
rtsp://ip:port/rtsp/playback?channel=1&subtype=0&starttime=2021-03-24T01:30:00Z&endtime=2021-03-24T07:30:59Z&localtime=true
```
- Request Body (JSON): No JSON request body sample was documented on this page.

### Record Configuration

#### Record Configuration

- Source page: `Record/Record Configuration/API.html`
- Purpose: This API is used for get or set Record Configuration page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/RecordConfig/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Record/Record Configuration/Get.html`
- Purpose: This API is used to get parameter for Record > Record Configuration page.
- Endpoint:
```http
POST http://000.00.00.000/API/RecordConfig/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `Record/Record Configuration/Range.html`
- Purpose: This API is used to get parameter range for Record > Record Configuration page.
- Endpoint:
```http
POST http://000.00.00.000/API/RecordConfig/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Record/Record Configuration/Set.html`
- Purpose: This API is used to set parameter for Record > Record Configuration page.
- Endpoint:
```http
POST http://000.00.00.000/API/RecordConfig/Set
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"channel_info": {
			"CH1": {
				"record_switch": true,
				"stream_mode": "DualStream",
				"prerecord": true,
				"anr": false,
				"copy_ch": "all",
				"chn_index": "CH1"
			},
			"CH2": {
				"record_switch": true,
				"stream_mode": "DualStream",
				"prerecord": true,
				"copy_ch": "all"
			},
			"CH3": {
				"record_switch": true,
				"stream_mode": "DualStream",
				"prerecord": true,
				"copy_ch": "all",
				"chn_index": "CH3"
			},
			"CH4": {
				"record_switch": true,
				"stream_mode": "DualStream",
				"prerecord": true,
				"copy_ch": "all"
			},
			"CH5": {
				"record_switch": true,
				"stream_mode": "DualStream",
				"prerecord": true,
				"copy_ch": "all"
			},
			"CH6": {
				"record_switch": true,
				"stream_mode": "DualStream",
				"prerecord": true,
				"copy_ch": "all"
			},
			"CH7": {
				"record_switch": true,
				"stream_mode": "DualStream",
				"prerecord": true,
				"copy_ch": "all"
			},
			"CH8": {
				"record_switch": true,
				"stream_mode": "DualStream",
				"prerecord": true,
				"copy_ch": "all"
			},
			"CH9": {
				"record_switch": true,
				"stream_mode": "DualStream",
				"prerecord": true,
				"copy_ch": "all"
			},
			"CH10": {
				"record_switch": true,
				"stream_mode": "DualStream",
				"prerecord": true,
				"copy_ch": "all"
			},
			"CH11": {
				"record_switch": true,
				"stream_mode": "DualStream",
				"prerecord": true,
				"copy_ch": "all"
			},
			"CH12": {
				"record_switch": true,
				"stream_mode": "DualStream",
				"prerecord": true,
				"copy_ch": "all"
			},
			"CH13": {
				"record_switch": true,
				"stream_mode": "DualStream",
				"prerecord": true,
				"copy_ch": "all"
			},
			"CH14": {
				"record_switch": true,
				"stream_mode": "DualStream",
				"prerecord": true,
				"copy_ch": "all"
			},
			"CH15": {
				"record_switch": true,
				"stream_mode": "DualStream",
				"prerecord": true,
				"copy_ch": "all"
			},
			"CH16": {
				"record_switch": true,
				"stream_mode": "DualStream",
				"prerecord": true,
				"copy_ch": "all"
			}
		}
	}
}
```

### Record Tag

#### Record Tag

- Source page: `Record/Record Tag/API.html`
- Purpose: This API is used to get or add a Record Tag.
- Endpoint:
```http
POST http://000.00.00.000/API/Playback/Tag/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Record/Record Tag/Get.html`
- Purpose: This API is used to get parameter for Record > Record Tag page.
- Endpoint:
```http
POST http://000.00.00.000/API/Playback/Tag/Get
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"start_date": "06/29/2023",
		"start_time": "00:00:00",
		"end_date": "06/29/2023",
		"end_time": "23:59:59",
		"channel": [
			"CH1",
			"CH2",
			"CH3",
			"CH4",
			"CH5",
			"CH6",
			"CH7",
			"CH8",
			"CH9",
			"CH10",
			"CH11",
			"CH12",
			"CH13",
			"CH14",
			"CH15",
			"CH16"
		],
		"Keyword": ""
	}
}
```

#### Range

- Source page: `Record/Record Tag/Range.html`
- Purpose: This API is used to get parameter range for Record >  Record Tag page.
- Endpoint:
```http
POST http://000.00.00.000/API/Playback/Tag/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Record/Record Tag/Set.html`
- Purpose: This API is used to set parameter for Record >  Record Tag page.
- Endpoint:
```http
POST http://000.00.00.000/API/Playback/Tag/Set
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"Tag_name": "Tag1",
		"Tag_date": "06/29/2023",
		"Tag_time": "13:19:40",
		"label_id": 0,
		"record_id": 0,
		"operate": 0,
		"channel": [
			"CH1"
		]
	}
}
```

### Search Record

#### Search Record

- Source page: `Record/Search Record/API.html`
- Purpose: This API is used to Search the Search Record page for playback data.
- Endpoint:
```http
POST http://000.00.00.000/API/Playback/SearchRecord/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Range

- Source page: `Record/Search Record/Range.html`
- Purpose: This API is used to obtain the Record > Search Record page playback data range.
- Endpoint:
```http
POST http://000.00.00.000/API/Playback/SearchRecord/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Search

- Source page: `Record/Search Record/Search.html`
- Purpose: This API is used to Search Record > Search Record page playback data.
- Endpoint:
```http
POST http://000.00.00.000/API/Playback/SearchRecord/Search
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"channel": [
			"CH1"
		],
		"start_date": "06/28/2023",
		"start_time": "00:00:00",
		"end_date": "06/28/2023",
		"end_time": "23:59:59",
		"record_type": 4294967295,
		"smart_region": [],
		"enable_smart_search": 0,
		"record_type_ex": [
			4294967295
		],
		"stream_mode": "Substream"
	}
}
```

## Storage

### Audio

#### Audio

- Source page: `Storage/Audio/API.html`
- Purpose: This API is used for get or set Audio page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/DeviceConfig/Audio/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Storage/Audio/Get.html`
- Purpose: This API is used to get parameter for Storage > Audio page.
- Endpoint:
```http
POST http://000.00.00.000/API/DeviceConfig/Audio/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `Storage/Audio/Range.html`
- Purpose: This API is used to get parameter range for Storage > Audio page.
- Endpoint:
```http
POST http://000.00.00.000/API/DeviceConfig/Audio/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Storage/Audio/Set.html`
- Purpose: This API is used to set parameter for Storage > Audio page.
- Endpoint:
```http
POST http://000.00.00.000/API/DeviceConfig/Audio/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {
            "CH1": {
                "audio_type": "G711A",
                "chn_index": "CH1",
                "copy_ch": "digit",
                "in_volume": 9,
                "out_volume": 9,
                "page": "device_audio"
            },
            "CH14": {
                "audio_enable": true,
                "audio_type": "G711A",
                "copy_ch": "digit",
                "in_volume": 0,
                "out_volume": 0
            }
        },
        "page_type": "ChannelConfig"
    }
}
```

### Cloud

#### accesstoken

- Source page: `Storage/Cloud/accesstoken.html`
- Purpose: This API is used to set parameter for Storage > Cloud page.
- Endpoint:
```http
POST http://000.00.00.000/API/action/accesstoken
```
- Request Body (JSON):
```json
{
    "result": "success",
    "data": {
        "accesstoken": "9cb768de6f3094faab02a6097192793661a844c74a87aa9621289d3e4304c5fb"
    }
}
```

#### Cloud

- Source page: `Storage/Cloud/API.html`
- Purpose: This API is used for get or set Cloud page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/StorageConfig/Cloud/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Control

- Source page: `Storage/Cloud/Control.html`
- Purpose: This API is used to set parameter for Storage > Cloud page.
- Endpoint:
```http
POST http://000.00.00.000/API/StorageConfig/Cloud/Control
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {
            "CH1": {
                "folder_name": "CH1", 
                "chn_index": "CH1"
            },
            "CH5": {
                "folder_name": "CH5"
            },
            "CH6": {
                "folder_name": "CH6"
            },
            "CH7": {
                "folder_name": "CH7"
            },
            "CH11": {
                "folder_name": "CH11"
            },
            "CH14": {
                "folder_name": "CH14"
            },
            "CH15": {
                "folder_name": "CH15"
            },
            "CH16": {
                "folder_name": "CH16"
            }
        },
        "cloud_over_write": "OFF",
        "cloud_status": "NetworkBlocked",
        "cloud_storage": true,
        "cloud_type": "DROPBOX",
        "progress": 0,
        "total_size": "0.00B",
        "used_size": "0.00B",
        "video_type": "RF"
    }
}
```

#### Get

- Source page: `Storage/Cloud/Get.html`
- Purpose: This API is used to set parameter for Storage > Cloud page.
- Endpoint:
```http
POST http://000.00.00.000/API/StorageConfig/Cloud/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `Storage/Cloud/Range.html`
- Purpose: This API is used to set parameter for Storage > Cloud page.
- Endpoint:
```http
POST http://000.00.00.000/API/StorageConfig/Cloud/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Storage/Cloud/Set.html`
- Purpose: This API is used to set parameter for Storage > Cloud page.
- Endpoint:
```http
POST http://000.00.00.000/API/StorageConfig/Cloud/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {
            "CH1": {
                "folder_name": "CH1", 
                "chn_index": "CH1"
            },
            "CH5": {
                "folder_name": "CH5"
            },
            "CH6": {
                "folder_name": "CH6"
            },
            "CH7": {
                "folder_name": "CH7"
            },
            "CH11": {
                "folder_name": "CH11"
            },
            "CH14": {
                "folder_name": "CH14"
            },
            "CH15": {
                "folder_name": "CH15"
            },
            "CH16": {
                "folder_name": "CH16"
            }
        },
        "cloud_over_write": "OFF",
        "cloud_status": "NetworkBlocked",
        "cloud_storage": true,
        "cloud_type": "DROPBOX",
        "progress": 0,
        "total_size": "0.00B",
        "used_size": "0.00B",
        "video_type": "RF"
    }
}
```

### Disk Group

#### Disk Group

- Source page: `Storage/Disk Group/API.html`
- Purpose: This API is used for get or set Disk Group page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/StorageConfig/DiskGroup/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Storage/Disk Group/Get.html`
- Purpose: This API is used to get parameter for Storage > Disk Group page.
- Endpoint:
```http
POST http://000.00.00.000/API/StorageConfig/DiskGroup/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `Storage/Disk Group/Range.html`
- Purpose: This API is used to get parameter for Storage > Disk Group page.
- Endpoint:
```http
POST http://000.00.00.000/API/StorageConfig/DiskGroup/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Storage/Disk Group/Set.html`
- Purpose: This API is used to get parameter for Storage > Disk Group page.
- Endpoint:
```http
POST http://000.00.00.000/API/StorageConfig/DiskGroup/Set
```
- Request Body (JSON):
```json
{
    "result": "success",
    "data": {
        "disk_group_info": [
            {
                "disk_group_type": "Record Disk Group",
                "group_array": [
                    {
                        "group_num": "Record Disk Group 1",
                        "channel": [
                            "CH1",
                            "IP_CH1",
                            "IP_CH2"
                        ]
                    },
                    {
                        "group_num": "Record Disk Group 2",
                        "channel": [
                            "CH2",
                            "CH3",
                            "CH4"
                        ]
                    }
                ]
            }
        ]
    }
}
```

### Disk

#### Disk

- Source page: `Storage/Disk/API.html`
- Purpose: This API is used for get or set Disk page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/StorageConfig/Disk/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

### Disk / Disk Configuration

#### Get

- Source page: `Storage/Disk/Disk Configuration/Get.html`
- Purpose: This API is used to set parameter for Storage > Disk page.
- Endpoint:
```http
POST http://000.00.00.000/API/StorageConfig/Disk/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `Storage/Disk/Disk Configuration/Range.html`
- Purpose: This API is used to get parameter range for Storage > Disk page.
- Endpoint:
```http
POST http://000.00.00.000/API/StorageConfig/Disk/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Storage/Disk/Disk Configuration/Set.html`
- Purpose: This API is used to set parameter for Storage > Disk page.
- Endpoint:
```http
POST http://000.00.00.000/API/StorageConfig/Disk/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "NasMaxCount": 1,
        "diskArr": [

        ],
        "disk_info": [
            {
                "delete_enable": false,
                "device_type": "Normal",
                "disk_type": "ReadAndWriteDisk",
                "display_id": 1,
                "firmware": "AX0U1Q",
                "format_enable": true,
                "free_size": 0,
                "free_time": 0,
                "id": 1,
                "model": "TOSHIBA MQ01ABD050V",
                "serial_no": "Z68ES299S",
                "status": "Full",
                "total_size": 476940,
                "total_time": 724487
            }
        ],
        "hdd_format_type": "AllHddData",
        "over_write": "Auto",
        "support_format": true
    }
}
```

### Disk / Disk Control

#### Control

- Source page: `Storage/Disk/Disk Control/Control.html`
- Purpose: This API is used to set parameter for Storage > Disk page.
- Endpoint:
```http
POST http://000.00.00.000/API/StorageConfig/Disk/Control
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "Info": {
            "Enable": 1,
            "Mode": "Edit",
            "disk_type": "ReadAndWriteDisk",
            "id": 1
        },
        "Type": "Hdd"
    }
}
```

### Disk / Disk Format

#### Format

- Source page: `Storage/Disk/Disk Format/Format.html`
- Purpose: This API is used to set parameter for Storage > Disk page.
- Endpoint:
```http
POST http://000.00.00.000/API/StorageConfig/Disk/Format
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "base_secondary_authentication": {
            "cipher": "oz+j5ICkAxtNjnxGInpxkOLHvsep6Fm5gruG6F0/PCE=",
            "seq": 1
        },
        "hdd_format_type": "AllHddData",
        "hdd_id": [
            1
        ]
    }
}
```

#### Progress

- Source page: `Storage/Disk/Disk Format/Progress.html`
- Purpose: This API is used to set parameter for Storage > Disk page.
- Endpoint:
```http
POST http://000.00.00.000/API/StorageConfig/Disk/Format/Progress
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

### RAID

#### RAID

- Source page: `Storage/RAID/API.html`
- Purpose: This API is used for get or set RAID page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/StorageConfig/Raid/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Storage/RAID/Get.html`
- Purpose: This API is used to get parameter for Storage > RAID page.
- Endpoint:
```http
POST http://000.00.00.000/API/StorageConfig/Raid/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `Storage/RAID/Range.html`
- Purpose: This API is used to get parameter range for Storage > RAID page.
- Endpoint:
```http
POST http://000.00.00.000/API/StorageConfig/Raid/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Storage/RAID/Set.html`
- Purpose: This API is used to get parameter for Storage > RAID page.
- Endpoint:
```http
POST http://000.00.00.000/API/StorageConfig/Raid/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "disk_info": [
            {
                "No": 0,
                "id": 3,
                "enable": false,
                "check": false,
                "slot_no": "HDD4",
                "disk_model": "TOSHIBA DT01ABA100V",
                "serial_no": "878UUN4MS",
                "total_size": 931,
                "array_name": "-",
                "disk_type": "Normal Disk",
                "button_type": "Add HotDisk"
            }
        ],
        "raid_info": [

        ],
        "about_raid_info": {
            "max_raid_num": 16,
            "raid_type": [
                0,
                1,
                5,
                6,
                10
            ],
            "hotdisk_type": "Global Hot Spare Disk",
            "support_rebuild": "Supported"
        },
        "create_raid": {
            "raid_type": "RAID0",
            "disk_info": [
                {
                    "id": 3,
                    "serial_no": "HDD4-878UUN4MS",
                    "slot_no": 1,
                    "enable": false,
                    "check": false
                }
            ]
        }
    }
}
```

## Stream

### Capture

#### Capture

- Source page: `Stream/Capture/API.html`
- Purpose: This API is used to get or set Capture page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/StreamConfig/Capture/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Stream/Capture/Get.html`
- Purpose: This API is used to get parameter for Stream > Capture page.
- Endpoint:
```http
POST http://000.00.00.000/API/StreamConfig/Capture/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `Stream/Capture/Range.html`
- Purpose: This API is used to get parameter range for Stream > Capture page.
- Endpoint:
```http
POST http://000.00.00.000/API/StreamConfig/Capture/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Stream/Capture/Set.html`
- Purpose: This API is used to set parameter for Stream > Capture page.
- Endpoint:
```http
POST http://000.00.00.000/API/StreamConfig/Capture/Set
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"channel_info": {
			"CH1": {
				"auto_capture": true,
				"normal_interval": 600,
				"alarm_interval": 60,
				"copy_ch": "all",
				"chn_index": "CH1"
			},
			"CH2": {
				"auto_capture": false,
				"normal_interval": 5,
				"alarm_interval": 5,
				"copy_ch": "all"
			},
			"CH3": {
				"auto_capture": false,
				"normal_interval": 5,
				"alarm_interval": 5,
				"copy_ch": "all"
			},
			"CH4": {
				"auto_capture": false,
				"normal_interval": 5,
				"alarm_interval": 5,
				"copy_ch": "all"
			},
			"CH5": {
				"auto_capture": false,
				"normal_interval": 5,
				"alarm_interval": 5,
				"copy_ch": "all"
			},
			"CH6": {
				"auto_capture": false,
				"normal_interval": 5,
				"alarm_interval": 5,
				"copy_ch": "all"
			},
			"CH7": {
				"auto_capture": false,
				"normal_interval": 5,
				"alarm_interval": 5,
				"copy_ch": "all"
			},
			"CH8": {
				"auto_capture": false,
				"normal_interval": 5,
				"alarm_interval": 5,
				"copy_ch": "all"
			},
			"CH9": {
				"auto_capture": false,
				"normal_interval": 5,
				"alarm_interval": 5,
				"copy_ch": "all"
			},
			"CH10": {
				"auto_capture": false,
				"normal_interval": 5,
				"alarm_interval": 5,
				"copy_ch": "all"
			},
			"CH11": {
				"auto_capture": false,
				"normal_interval": 5,
				"alarm_interval": 5,
				"copy_ch": "all"
			},
			"CH12": {
				"auto_capture": false,
				"normal_interval": 5,
				"alarm_interval": 5,
				"copy_ch": "all"
			},
			"CH13": {
				"auto_capture": false,
				"normal_interval": 5,
				"alarm_interval": 5,
				"copy_ch": "all"
			},
			"CH14": {
				"auto_capture": false,
				"normal_interval": 5,
				"alarm_interval": 5,
				"copy_ch": "all"
			},
			"CH15": {
				"auto_capture": false,
				"normal_interval": 5,
				"alarm_interval": 5,
				"copy_ch": "all"
			},
			"CH16": {
				"auto_capture": false,
				"normal_interval": 5,
				"alarm_interval": 5,
				"copy_ch": "all"
			}
		}
	}
}
```

### Encode

#### Encode

- Source page: `Stream/Encode/API.html`
- Purpose: This API is used to get or set MainStream, SubStream, MobileStream, and EventStream page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/StreamConfig/{Page}/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Stream/Encode/Get.html`
- Purpose: This API is used to get parameter for Stream > Encode page.
- Endpoint:
```http
POST http://000.00.00.000/API/StreamConfig/MainStream/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `Stream/Encode/Range.html`
- Purpose: This API is used to get parameter range for Stream > Encode page.
- Endpoint:
```http
POST http://000.00.00.000/API/StreamConfig/MainStream/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `Stream/Encode/Set.html`
- Purpose: This API is used to set parameter for Stream > Encode page.
- Endpoint:
```http
POST http://000.00.00.000/API/StreamConfig/MainStream/Set
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"channel_info": {
			"CH1": {
				"rtsp_enable": false,
				"stream_type": "Normal",
				"video_encode_type": "H.265",
				"resolution": "1920 x 1080",
				"fps": 30,
				"bitrate_control": "CBR",
				"video_quality": "Highest",
				"bitrate_mode": "Predefined",
				"bitrate": 2048,
				"custom_bitrate": 2048,
				"audio": true,
				"i_frame_interval": 60,
				"etr": false,
				"etr_stream_type": "Alarm",
				"etr_resolution": "1920 x 1080",
				"etr_fps": 30,
				"etr_video_encode_type": "H.265",
				"etr_bitrate_control": "CBR",
				"etr_video_quality": "Highest",
				"etr_bitrate_mode": "Predefined",
				"etr_bitrate": 4096,
				"etr_custom_bitrate": 4096,
				"etr_audio": true,
				"etr_i_frame_interval": 60,
				"chn_index": "CH1"
			},
			"CH14": {
				"rtsp_enable": false,
				"stream_type": "Normal",
				"video_encode_type": "H.264",
				"resolution": "1920 x 1080",
				"fps": 25,
				"bitrate_control": "CBR",
				"video_quality": "Highest",
				"bitrate_mode": "UserDefined",
				"bitrate": 256,
				"custom_bitrate": 1024,
				"audio": true,
				"i_frame_interval": 50
			},
			"CH16": {
				"rtsp_enable": false,
				"stream_type": "Normal",
				"video_encode_type": "H.264+",
				"resolution": "2560 x 1440",
				"fps": 30,
				"bitrate_control": "CBR",
				"video_quality": "Highest",
				"bitrate_mode": "Predefined",
				"bitrate": 6144,
				"custom_bitrate": 6144,
				"audio": true,
				"i_frame_interval": 60,
				"etr": false,
				"etr_stream_type": "Alarm",
				"etr_resolution": "2560 x 1440",
				"etr_fps": 30,
				"etr_video_encode_type": "H.265",
				"etr_bitrate_control": "CBR",
				"etr_video_quality": "Highest",
				"etr_bitrate_mode": "Predefined",
				"etr_bitrate": 4096,
				"etr_custom_bitrate": 4096,
				"etr_audio": true,
				"etr_i_frame_interval": 120
			}
		}
	}
}
```

### Rtsp Url

#### Rtsp Url

- Source page: `Stream/Rtsp Url/API.html`
- Purpose: This API is used to access the device RTSP Real-time streaming.
- Endpoint:
```http
POST http://000.00.00.000/API/Preview/StreamUrl/Get/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Stream/Rtsp Url/Get.html`
- Purpose: This API is used to get parameter for Stream > Rtsp Url page.
- Endpoint:
```http
POST http://000.00.00.000/API/Preview/StreamUrl/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

## System

### Channel Information

#### Channel Information

- Source page: `System/Channel Information/API.html`
- Purpose: This API is used for get or set Channel Information parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/Channel/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `System/Channel Information/Get.html`
- Purpose: This API is used to get parameter for System > Channel Information page.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemInfo/Channel/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

### Date&Time

#### Data&Time

- Source page: `System/Date&Time/API.html`
- Purpose: This API is used for get or set Data&Time page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/DateTime/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `System/Date&Time/Get.html`
- Purpose: This API is used to get parameter for System > Date&Time page.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/DateTime/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `System/Date&Time/Range.html`
- Purpose: This API is used to get parameter range for System > Date&Time page.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/DateTime/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `System/Date&Time/Set.html`
- Purpose: This API is used to set parameter for System > Date&Time page.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/DateTime/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "date_format": "MM/DD/YYYY",
        "time_format": 12,
        "time_zone": "GMT+8:00"
    }
}
```
```json
{
    "version": "1.0",
    "data": {
		"date": "01/01/1970",
		"time": "00:00:00",
        "date_format": "MM/DD/YYYY",
        "time_format": 12,
        "time_zone": "GMT+8:00"
    }
}
```

### DST

#### DST

- Source page: `System/DST/API.html`
- Purpose: This API is used for get or set Daylight Saving Time (DST) page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/DST/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `System/DST/Get.html`
- Purpose: This API is used to get parameter for System > DST page.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/DST/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
}
```

#### Range

- Source page: `System/DST/Range.html`
- Purpose: This API is used to get the parameter range of the System > DST page
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/DST/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `System/DST/Set.html`
- Purpose: This API is used to set parameter for System > DST page.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/DST/Set
```
- Request Body (JSON):
```json
{
	"data": {
		"dst_enable": true,
		"dst_mode": "Week",
		"end_date": "01/03/2022",
		"end_hour": "04:00:00",
		"end_month": "Mar",
		"end_week": "3rd",
		"end_weekday": "Mon",
		"start_date": "10/10/2021",
		"start_hour": "02:00:00",
		"start_month": "Apr",
		"start_week": "4th",
		"start_weekday": "Mon",
		"support_crossyear": true,
		"time_offset": 1
	},
	"version": "1.0"
}
```

### General

#### General

- Source page: `System/General/API.html`
- Purpose: This API is used for get or set General page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/General/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `System/General/Get.html`
- Purpose: This API is used to get parameter for System > General page.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/General/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `System/General/Range.html`
- Purpose: This API is used to get parameter range for System > General page.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/General/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `System/General/Set.html`
- Purpose: This API is used to set parameter for System > General page.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/General/Set
```
- Request Body (JSON):
```json
{
	"version": "1.0",
	"data": {
		"device_name": "admin",
		"menu_timeouts": 60,
		"session_timeout": 1440,
		"preview_session_timeout": false
	}
}
```

### Network State

#### Network State

- Source page: `System/Network State/API.html`
- Purpose: This API is used for get or set Network State page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemInfo/Network/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `System/Network State/Get.html`
- Purpose: This API is used to get parameter for System > Network State page.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemInfo/Network/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

### NTP

#### General

- Source page: `System/NTP/API.html`
- Purpose: This API is used for get or set NTP page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/NTP/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `System/NTP/Get.html`
- Purpose: This API is used to get parameter for System > NTP page.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/NTP/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `System/NTP/Range.html`
- Purpose: This API is used to get parameter range for System > NTP page.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/NTP/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `System/NTP/Set.html`
- Purpose: This API is used to set parameter for System > NTP page.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/NTP/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "ntp_enable": false,
        "server": "pool.ntp.org",
        "custom_server": ""
    }
}
```

### Output

#### Output

- Source page: `System/Output/API.html`
- Purpose: This API is used for get or set Output page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/Output/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `System/Output/Get.html`
- Purpose: This API is used to get parameter for System > Output page.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/Output/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `System/Output/Range.html`
- Purpose: This API is used to get parameter range for System > Output page.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/Output/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Set

- Source page: `System/Output/Set.html`
- Purpose: This API is used to set parameter for System > Output page.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/Output/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "output": {
            "LIVE-OUT": {
                "output_resolution": "1280x1024"
            }
        }
    }
}
```

### Privacy Statement

#### Privacy Statement

- Source page: `System/Privacy Statement/API.html`
- Purpose: This API is used for get or set Privacy Statement page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/Statement/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `System/Privacy Statement/Get.html`
- Purpose: This API is used to get parameter for System > Privacy Statement page.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/Statement/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

#### Range

- Source page: `System/Privacy Statement/Range.html`
- Purpose: This API is used to get parameter range for System > Privacy Statement page.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemConfig/Statement/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

### Record Information

#### Record Information

- Source page: `System/Record Information/API.html`
- Purpose: This API is used for get or set Record Information page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemInfo/Record/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `System/Record Information/Get.html`
- Purpose: This API is used to get parameter for System > Record Information page.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemInfo/Record/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

### System Information

#### System Information

- Source page: `System/System Information/API.html`
- Purpose: This API is used for get or set System Information page parameters.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemInfo/Base/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `System/System Information/Get.html`
- Purpose: This API is used to get parameter for System > System Information page.
- Endpoint:
```http
POST http://000.00.00.000/API/SystemInfo/Base/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {}
}
```

## Thermal

### Fire Detection

#### Add

- Source page: `Thermal/Fire Detection/Add.html`
- Purpose: This API is used for adding Thermal > Fire Detection parameter
- Endpoint:
```http
POST http://000.00.00.000/API/Thermal/Setup/FireDetection/Add
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel": "CH2",
        "page_type": "ChannelConfig"
    }
}
```

#### Fire Detection(Thermal imaging channel CH2 support)

- Source page: `Thermal/Fire Detection/API.html`
- Purpose: This API is used to get or set for the Fire Detection parameter.
- Endpoint:
```http
POST http://000.00.00.000/API/Thermal/Setup/FireDetection/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Delete

- Source page: `Thermal/Fire Detection/Delete.html`
- Purpose: This API is used for deletion Thermal > Fire Detection parameter
- Endpoint:
```http
POST http://000.00.00.000/API/Thermal/Setup/FireDetection/Delete
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel": "CH2",
        "page_type": "ChannelConfig",
        "DeleteId": [2]
    }
}
```

#### Get

- Source page: `Thermal/Fire Detection/Get.html`
- Purpose: This API is used for get Thermal > Fire Detection parameter
- Endpoint:
```http
POST http://000.00.00.000/API/Thermal/Setup/FireDetection/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data":{
        "page_type":"ChannelConfig"
        }

}
```

#### Range

- Source page: `Thermal/Fire Detection/Range.html`
- Purpose: This API is used for get Thermal > Fire Detection parameter scale
- Endpoint:
```http
POST http://000.00.00.000/API/Thermal/Setup/FireDetection/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data":{
        "page_type":"ChannelConfig"
        }

}
```

#### Set

- Source page: `Thermal/Fire Detection/Set.html`
- Purpose: This API is used for setting Thermal > Fire Detection parameter.
- Endpoint:
```http
POST http://000.00.00.000/API/Thermal/Setup/FireDetection/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {"CH2": {
            "status": "Online",
            "detection": {
                "switch": true,
                "sensitivity": 50
            },
            "region_shield": {"region_area_info": [{
                "id_switch": true,
                "area_id": 1,
                "area_name": "Fire Mark1",
                "point_num": [
                    3,
                    8
                ],
                "rule_area": {
                    "x1": 0,
                    "y1": 0,
                    "x2": 0,
                    "y2": 0,
                    "x3": 0,
                    "y3": 0,
                    "x4": 0,
                    "y4": 0,
                    "x5": 0,
                    "y5": 0,
                    "x6": 0,
                    "y6": 0,
                    "x7": 0,
                    "y7": 0,
                    "x8": 0,
                    "y8": 0
                }
            }]},
            "chn_index": "CH2",
            "page": "chn_fire_detection",
            "selectEditRow": 0
        }},
        "page_type": "ChannelConfig"
    }
}
```

### Image Control

#### Image Control (IPC: Optical channel: CH1, thermal imaging channel: CH2)

- Source page: `Thermal/Image Control/API.html`
- Purpose: This API is used to get or set for ImageControl Thermal imaging channel parameters
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ImageControl/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Default

- Source page: `Thermal/Image Control/Default.html`
- Purpose: This API is used to restore defaults Thermal > ImageControl parameter
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ImageControl/Default
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"channel": ["CH2"]}
}
```

#### Get

- Source page: `Thermal/Image Control/Get.html`
- Purpose: This API is used for get Thermal > ImageControl parameter
- Endpoint:
```http
HTTP/1.1 200 OK
Content-Type: application/json
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### InfraredCorr

- Source page: `Thermal/Image Control/InfraredCorr.html`
- Purpose: This API is used for get InfrareCorr Thermal > ImageControl parameter
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ImageControl/InfrareCorr
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel": "CH2",
        "infrared_corr_type": "ShutterCorr"
    }
}
```

#### Range

- Source page: `Thermal/Image Control/Range.html`
- Purpose: This API is used for get Thermal > ImageControl parameter scale
- Endpoint:
```http
HTTP/1.1 200 OK
Content-Type: application/json
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Set

- Source page: `Thermal/Image Control/Set.html`
- Purpose: This API is used for set Thermal > ImageControl page.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/ImageControl/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"channel_info": {
        "CH1": {
            "status": "Online",
            "image_setting": "DayNightMode",
            "DayNightMode": {
                "ir_cut_mode": "Image",
                "image_sensitivity": 1,
                "ir_led": "Manual",
                "low_beam_light": 100
            },
            "mirror_mode": "Close",
            "angle_rotation": "0",
            "Daylight": {
                "back_light": "Close",
                "blc_level": 2,
                "back_light_area": "Center",
                "denoising": "Auto",
                "white_balance": "Auto",
                "exposure_mode": "Auto",
                "shutter_limit": "1/8"
            },
            "support_default": true
        },
        "CH2": {
            "status": "Online",
            "mirror_mode": "Close",
            "angle_rotation": "0",
            "denoising_2dlevel": 50,
            "denoising_3dlevel": 50,
            "enhancement_level": 50,
            "enhance_regional": "Disable",
            "rule_info": [{
                "rule_no": 1,
                "rule_rect": {
                    "left": 0,
                    "top": 0,
                    "width": 0,
                    "height": 0
                },
                "Select": 0
            }],
            "palette": "Rainbow",
            "fusion": "Normal",
            "imagefusion_level": 50,
            "edgefusion_level": 50,
            "horizontal_trim": 0,
            "vertica_trim": 0,
            "fusion_distance": 2,
            "support_backgroundcorr": true,
            "support_shuttercorr": true,
            "support_default": true,
            "chn_index": "CH2",
            "page": "chn_imgCtrl",
            "camera_param_mode": "Daylight",
            "Daylight": {}
        }
    }}
}
```

### Measurement Rule

#### Add

- Source page: `Thermal/Measurement Rule/Add.html`
- Purpose: This API is used to add Thermal > Measurement Rule parameter
- Endpoint:
```http
POST http://000.00.00.000/API/Thermal/Setup/MeasurementRules/Add
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"channel": "CH2"}
}
```

#### Measurement Rule(Thermal imaging channel CH2 support)

- Source page: `Thermal/Measurement Rule/API.html`
- Purpose: This API is used to get or set for MeasurementRule parameter.
- Endpoint:
```http
POST http://000.00.00.000/API/Thermal/Setup/MeasurementRules/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Delete

- Source page: `Thermal/Measurement Rule/Delete.html`
- Purpose: This API is used to delete Thermal > Measurement Rule parameter
- Endpoint:
```http
POST http://000.00.00.000/API/Thermal/Setup/MeasurementRules/Delete
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel": "CH2",
        "DeleteId": [1]
    }
}
```

#### Get

- Source page: `Thermal/Measurement Rule/Get.html`
- Purpose: This API is used to get parameter for Thermal > Measurement Rule page.
- Endpoint:
```http
POST http://000.00.00.000/API/Thermal/Setup/MeasurementRules/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data":{
        "page_type":"ChannelConfig"
        }

}
```

#### Range

- Source page: `Thermal/Measurement Rule/Range.html`
- Purpose: This API is used to get Thermal > Measurement Rule parameter scale
- Endpoint:
```http
POST http://000.00.00.000/API/Thermal/Setup/MeasurementRules/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data":{
        "page_type":"ChannelConfig"
        }

}
```

#### Set

- Source page: `Thermal/Measurement Rule/Set.html`
- Purpose: This API is used to set Thermal > Measurement Rule page
- Endpoint:
```http
POST http://000.00.00.000/API/Thermal/Setup/MeasurementRules/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {"CH2": {
            "status": "Online",
            "switch": true,
            "colorbar_switch": false,
            "display_temp_on_optical": false,
            "display_temp_on_stream": true,
            "display_max_temp": true,
            "display_min_temp": false,
            "display_average_temp": false,
            "display_pos": "Near Target",
            "spot_measurement": false,
            "data_refresh_rate": "3",
            "temp_unit": "Degree Celsius",
            "emissivity": 0.96,
            "distance_unit": "Meter",
            "target_distance": 1,
            "reflective_temp": 20,
            "chn_index": "CH2",
            "page": "chn_measurement"
        }},
        "page_type": "ChannelConfig"
    }
}
```

### Measurement

#### Measurement(Thermal imaging channel CH2 support)

- Source page: `Thermal/Measurement/API.html`
- Purpose: This API is used to get or set for Measurement parameter.
- Endpoint:
```http
POST http://000.00.00.000/API/Thermal/Setup/Measurement/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Get

- Source page: `Thermal/Measurement/Get.html`
- Purpose: This API is used to get Thermal > Measurement parameter.
- Endpoint:
```http
POST http://000.00.00.000/API/Thermal/Setup/Measurement/Get
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data":{
        "page_type":"ChannelConfig"
        }

}
```

#### Range

- Source page: `Thermal/Measurement/Range.html`
- Purpose: This API is used to get Thermal > Measurement parameter scale
- Endpoint:
```http
POST http://000.00.00.000/API/Thermal/Setup/Measurement/Range
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data":{
        "page_type":"ChannelConfig"
        }

}
```

#### Set

- Source page: `Thermal/Measurement/Set.html`
- Purpose: This API is used to set Thermal > Measurement parameter.
- Endpoint:
```http
POST http://000.00.00.000/API/Thermal/Setup/Measurement/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {
        "channel_info": {"CH2": {
            "status": "Online",
            "switch": true,
            "colorbar_switch": false,
            "display_temp_on_optical": false,
            "display_temp_on_stream": true,
            "display_max_temp": true,
            "display_min_temp": false,
            "display_average_temp": false,
            "display_pos": "Near Target",
            "spot_measurement": false,
            "data_refresh_rate": "3",
            "temp_unit": "Degree Celsius",
            "emissivity": 0.96,
            "distance_unit": "Meter",
            "target_distance": 1,
            "reflective_temp": 20,
            "chn_index": "CH2",
            "page": "chn_measurement"
        }},
        "page_type": "ChannelConfig"
    }
}
```

### Spot Measurement

#### Spot Measurement

- Source page: `Thermal/Spot Measurement/API.html`
- Purpose: This API is used to get for Spot Measurement parameter.
- Endpoint:
```http
POST http://000.00.00.000/PreviewChannel/PreviewShowTempByPos/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Set

- Source page: `Thermal/Spot Measurement/Get.html`
- Purpose: This API is used to get Thermal > Spot Measurement parameter
- Endpoint:
```http
POST http://000.00.00.000/API/PreviewChannel/PreviewShowTempByPos/Get
```
- Request Body (JSON):
```json
{
    "data": {
       "channel":"CH2",
       "x":10,
       "y":20
    }
}
```

### Video Color

#### Video Color (IPC: Optical channel: CH1, Thermal imaging channel: CH2)

- Source page: `Thermal/Video Color/API.html`
- Purpose: This API is used to get or set Video Color Thermal imaging channel parameters
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/Color/{Action}
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Default

- Source page: `Thermal/Video Color/Default.html`
- Purpose: This API is used to restore default parameter for Thermal > Video Color page.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/Color/Default
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"channel": ["CH1"]}
}
```

#### Get

- Source page: `Thermal/Video Color/Get.html`
- Purpose: This API is used to get Thermal > Video Color parameter
- Endpoint:
```http
HTTP/1.1 200 OK
Content-Type: application/json
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Range

- Source page: `Thermal/Video Color/Range.html`
- Purpose: This API is used to get Thermal > Video Color parameter scale
- Endpoint:
```http
HTTP/1.1 200 OK
Content-Type: application/json
```
- Request Body (JSON): No JSON request body sample was documented on this page.

#### Set

- Source page: `Thermal/Video Color/Set.html`
- Purpose: This API is used to Set Thermal > Video Color page.
- Endpoint:
```http
POST http://000.00.00.000/API/ChannelConfig/Color/Set
```
- Request Body (JSON):
```json
{
    "version": "1.0",
    "data": {"channel_info": {"CH1": {
        "status": "Online",
        "bright": 128,
        "contrast": 128,
        "support_default": true,
        "hue": 167,
        "saturation": 128,
        "sharpness": 128,
        "last_hue": 50,
        "last_bright": 50,
        "last_contrast": 50,
        "last_saturation": 50,
        "last_sharpness": 50,
        "SunRise_time": "00:00",
        "SunSet_time": "00:00",
        "palette": "Rainbow"
    }}}
}
```

