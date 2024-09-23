// export const Settings: ISettings = {
//     user: '',
//     name: '',
//     instructions: '',
//     ci: true,
//     ciFiles: '',
//     fs: false,
//     fsFiles: '',
//     vs_name: '',
//   }

// export const RunningAssistant: IRunningAssistant = {
//     assistant_id: '',
//     thread_id: '',
//     files: [],
//   }

export interface ISettings {
    user: string,
    name: string,
    instructions: string,
    useTools: boolean,
    ci: boolean,
    ciFileURLs: string,
    fs: boolean,
    vs_name: string,
    fsFileURLs: string,
}


export interface IRunningAssistant {
    assistant_id: string,
    thread_id: string,
    files: string[],
}

export interface IThreadMessage {
    role: string,
    content: string,
    imageContent: string,
}



export interface IAssistantCreateRequest {
    userName: string,
    name: string,
    instructions: string,
    useTools: boolean,
    ci: boolean,
    ciFileURLs: string[],
    fs: boolean,
    vs_name: string,
    fsFileURLs: string[],
}

export interface IAssistantCreateResponse {
    userName: string,
    assistant_id: string,
    thread_id: string,
    file_ids: string[],
}

export interface IKVStoreItem {
    username: string,
    key: string,
    value: string
}

export interface IResponseMessage {
    role: string,
    content: string,
    imageContent: string,
}