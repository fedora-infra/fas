# -*- coding: utf-8 -*-

def jpeg(info):
    def render(data, system):
        request = system.get('request')
        if request is not None:
            response = request.response
            ct = response.content_type
            if ct == response.default_content_type:
                response.content_type = 'image/jpeg'

        return data.tostring('jpeg', 'RGB')
    return render