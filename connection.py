from GlobalDictionaryProxy import create_connection
from rx3.subject import Subject
import debugpy
from rx3 import operators as ops

_requests = {}


# def _on_data_test(data):
#     print(f'open subject {data}')

# def _on_data_test_filter(data):
#     print(f'filtered subject {data}')


connection = create_connection("TS_PLAT_API")

#connection.subject.subscribe(_on_data_test)

def send_request(request):

    id = request['id']

    if id not in _requests:
        # subject = Subject()
        _requests[id] = True


    #debugpy.breakpoint()	

    subject = connection.subject.pipe( ops.filter(lambda data: data['key']==id), ops.map(lambda data: data['value']))

    #subject.subscribe(_on_data_test_filter)

    #even if it exits it will requery the data
    connection.dictionary['request'] = request

    return subject



if __name__ == "__main__":
    subject = send_request({
        'id': "Data"
    })

    subject.subscribe(lambda x: print("Original subscriber value is {0}".format(x)))


    input("Enter any key")