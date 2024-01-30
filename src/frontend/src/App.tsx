import { makePersisted } from '@solid-primitives/storage'
import axios from 'axios'
import { For, createSignal } from 'solid-js'
import { SolidMarkdown } from 'solid-markdown'
import { Spinner, SpinnerType } from 'solid-spinner'
// import solidLogo from './assets/solid.svg'
// import viteLogo from '/vite.svg'
//import './App.css'

//const BaseURL = '/api/'
const BaseURL = 'http://127.0.0.1:8000/api/'
const POST_CREATE = BaseURL + 'create'
const POST_PROCESS = BaseURL + 'process'
const GET_STATUS = BaseURL + 'status?userName={name}'
const DELETE_ASSISTANT = BaseURL + 'delete?userName={name}'

interface ISettings {
  user: string,
  name: string,
  instructions: string,
  files: string,
}

const Settings = {
  user: 'user@email.com',
  name: 'CSV Assistant',
  instructions: 'You are an Assistant that can help analyze and perform calculations using the provided file(s). You are polite and friendly. After answering the user\'s, say, "Can I be of further assistance."',
  files: 'https://alemoraoaist.z13.web.core.windows.net/docs/Energy/wind_turbines_telemetry.csv',
}

interface IRunningAssistant {
  assistant_id: string,
  thread_id: string,
  files: string[],
}

interface IThreadMessage {
  role: string,
  content: string,
  imageContent: string,
}

const RunningAssistant: IRunningAssistant = {
  assistant_id: '',
  thread_id: '',
  files: [],
}

interface IAssistantCreateRequest {
  userName: string,
  name: string,
  instructions: string,
  fileURLs: string[],
}

interface IAssistantCreateResponse {
  userName: string,
  assistant_id: string,
  thread_id: string,
  file_ids: string[],
}

interface IKVStoreItem {
  username: string,
  key: string,
  value: string
}

interface IResponseMessage {
  role: string,
  content: string,
  imageContent: string,
}

function App() {
  const [settings, setSettings] = makePersisted(createSignal<ISettings>(Settings))
  const [runningAssistant, setRunningAssistant] = createSignal<IRunningAssistant>(RunningAssistant)
  const [threadMessages, setThreadMessages] = createSignal<IThreadMessage[]>([])
  const [prompt, setPrompt] = createSignal<string>('')
  const [processing, setProcessing] = createSignal<boolean>(false)

  const UpdateStatus = async () => {
    try {
      const resp = await axios.get<IKVStoreItem[]>(GET_STATUS.replace('{name}', settings().user))
      const data = resp.data
      if (resp.data.length === 0) return
      const assistant_id = data.filter((item) => item.key === 'assistant')[0].value
      const thread_id = data.filter((item) => item.key === 'thread')[0].value
      const files = data.filter((item) => item.key === 'file').map((item) => item.value)
      setRunningAssistant({ ...runningAssistant(), assistant_id, thread_id, files })
    } catch (err) {
      console.log(err)
    }
  }

  setInterval(async () => await UpdateStatus(), 2000);

  const CreateAssistant = async () => {
    if (processing()) return
    if (runningAssistant().assistant_id !== '') {
      alert('An AI Assistant is already running. Please delete it before creating a new one.')
      return
    }
    if (settings().user === '' || settings().name === '' || settings().instructions === '' || settings().files === '') {
      alert('User ID, Assistant Name, Instructions and files are required to create an AI Assistant.')
      return
    }

    setProcessing(true)
    const fileURLs = settings().files.split(',').map((file) => file.trim())
    const payload: IAssistantCreateRequest = {
      userName: settings().user,
      name: settings().name,
      instructions: settings().instructions,
      fileURLs,
    }
    //alert(JSON.stringify(payload))
    try {
      await axios.post<IAssistantCreateResponse>(POST_CREATE, payload)
      //const data = response.data
      //setRunningAssistant({ ...runningAssistant(), assistant_id: data.assistant_id, thread_id: data.thread_id, files: data.file_ids })
      await UpdateStatus()
    }
    catch (err) {
      console.log(err)
    }
    finally {
      setProcessing(false)
    }
  }

  const Process = async () => {
    if (processing()) return
    try {
      const payload: { userName: string, prompt: string } = {
        userName: settings().user,
        prompt: prompt()
      }
      setProcessing(true)
      const response = await axios.post<IResponseMessage[]>(POST_PROCESS, payload)
      const additional_messages = response.data
      setThreadMessages([...threadMessages(), ...additional_messages])
      setPrompt('')
    }
    catch (err) {
      console.log(err)
    }
    finally {
      setProcessing(false)
    }
  }

  const DeleteAssistant = async () => {
    try {
      const ask = confirm('Are you sure you want to delete the AI Assistant?')
      if (!ask) return
      setProcessing(true)
      const response = await axios.delete(DELETE_ASSISTANT.replace('{name}', settings().user))
      console.log(response)
      setPrompt('')
      setThreadMessages([])
      setRunningAssistant({ ...runningAssistant(), assistant_id: '', thread_id: '', files: [] })
    }
    catch (err) {
      console.log(err)
    }
    finally {
      setProcessing(false)
    }
  }

  const LoadSampleData = () => {
    const sampleSettings: ISettings = {
      user: 'user@email.com',
      name: 'Personalized Assistant',
      instructions: 'You are an Assistant that can help analyze and perform calculations on the provided data file(s). Use only the provided data. Be polite, friendly, and helpful. After answering a user\'s question, say, "Can I be of further assistance."',
      files: 'https://alemoraoaist.z13.web.core.windows.net/docs/Energy/wind_turbines_telemetry.csv',
    }
    setSettings({ ...settings(), ...sampleSettings })
    setPrompt('Generate a chart of the latest MSFT, APPL, TSLA and NVDIA stock prices?')
  }

  const StatusBarColor = () => {
    if (processing())
      return 'bg-red-600'

    if (runningAssistant().assistant_id === '')
      return 'bg-slate-500'
    else
      return 'bg-slate-900'
  }

  return (
    <>
      <header class="bg-slate-950 text-white p-3 text-2xl font-bold h-[60px]">Assistants API Playground</header>
      <div class="flex flex-row h-[calc(100vh-100px)]">
        <aside class="bg-slate-200 p-2 w-1/4 overflow-auto">
          <div class="flex flex-col p-3 space-y-2">
            <label class="uppercase font-bold border-b-2 border-slate-800 text-lg">Assistant Settings</label>
            <label class="uppercase font-semibold">User</label>
            <input class='p-1 outline-none' type="email"
              onchange={(e) => setSettings({ ...settings(), user: e.target.value })}
              value={settings().user}
            />
            <label class="uppercase font-semibold">Assistant Name</label>
            <input class='p-1 outline-none' type="text"
              onchange={(e) => setSettings({ ...settings(), name: e.target.value })}
              value={settings().name}
            />
            <label class="uppercase font-semibold">Instructions</label>
            <textarea class='p-1 outline-none'
              rows={5}
              onchange={(e) => setSettings({ ...settings(), instructions: e.target.value })}
              value={settings().instructions}
            />
            <label class="uppercase font-semibold">Files URLs</label>
            <textarea
              class='p-1 outline-none'
              rows={5}
              onchange={(e) => setSettings({ ...settings(), files: e.target.value })}
              value={settings().files}
            />
            <span class='bg-yellow-200 text-black p-2'><strong>Note: </strong>You can provide a comma separated list of files.</span>
          </div>
          <div class="flex flex-row space-x-2 p-3">
            <button class='w-20 p-2 bg-blue-700 text-white font-semibold'
              onclick={CreateAssistant}
            >Create</button>
            <button class='w-20 p-2 bg-blue-700 text-white font-semibold'
              onclick={DeleteAssistant}
            >Delete</button>
            <button class='w-20 p-2 bg-blue-700 text-white font-semibold'
              onclick={LoadSampleData}
            >Sample</button>
          </div>
          <div class="flex flex-col p-3 space-y-2">
            <label class="uppercase font-bold border-b-2 border-slate-800 text-lg">Available Tools</label>
            <span class='bg-blue-700 text-white rounded-xl p-1 w-24'>Stock Prices</span>
            <span class='bg-blue-700 text-white rounded-xl p-1 w-24'>Email</span>
            <label class="uppercase font-bold border-b-2 border-slate-800 text-lg">Uploaded Files</label>
            <For each={runningAssistant().files}>
              {(file) => (
                <div class='flex flex-col bg-slate-400 rounded p-1 space-y-2'>
                  <label><strong>ID:</strong> {JSON.parse(file).id}</label>
                  <label><strong>FILE:</strong> {JSON.parse(file).name}</label>
                </div>
              )}
            </For>
          </div>
        </aside>
        <main class="p-3 w-3/4 flex flex-col overflow-auto">
          <div class="flex flex-col">
            <div class="flex flex-row">
              <textarea class='outline-none p-2 w-full bg-blue-100 rounded'
                onchange={(e) => setPrompt(e.target.value)}
                value={prompt()}
                rows={5}></textarea>
              <button class='p-1 bg-blue-800 hover:bg-blue-700 font-semibold text-white'
                onclick={Process}
              >Search</button>
            </div>
            <For each={threadMessages()}>
              {(message) => (
                <div class='space-y-2 w-full mt-3'>
                  {/* <div class='w-[90%]'>{message.role}</div> */}
                  <div class={'w-[90%] p-2 rounded ' + (message.role === "user" ? "bg-blue-300" : "bg-blue-400 mx-auto")}><SolidMarkdown children={message.content} /></div>
                  <img class='w-[90%]' src={message.imageContent} alt="" />
                </div>
              )}
            </For>
          </div>
        </main>
      </div>
      <section class={"flex flex-wrap text-sm space-x-2 items-center h-[40px] text-white " + StatusBarColor()}>
        <span class={"bg-green-700 p-2 text-white uppercase " + (runningAssistant().assistant_id ? "visible" : "hidden")}>Assistant Loaded</span>
        <div class='space-x-2 p-2'><label class='uppercase font-semibold'>Assistant ID:</label><span class='p-1 bg-slate-800 text-white'>{runningAssistant().assistant_id}</span></div>
        <div class='space-x-2 p-2'><label class='uppercase font-semibold'>Thread ID:</label><span class='p-1 bg-slate-800 text-white'>{runningAssistant().thread_id}</span></div>
        <div class='space-x-2 p-2'><label class='uppercase font-semibold'>Files Loaded:</label><span class='p-1 bg-slate-800 text-white'>{runningAssistant().files.length}</span></div>
        <span class={(processing() ? "visible" : "hidden")}><Spinner type={SpinnerType.puff} color="white" height={25} /></span>
      </section >
    </>
  )
}

export default App
